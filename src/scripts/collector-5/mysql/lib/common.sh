#!/usr/bin/env bash
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Set strict error handling
set -euo pipefail

# Constants
readonly VERSION="4.3.39"
readonly REQUIRED_COMMANDS="cat cut dirname grep locale mkdir sed tar tr which mysql"
readonly SUPPORTED_SHELLS="bash ksh zsh sh"

# Detect OS and set OS-specific variables
detect_os() {
  case "$(uname -s)" in
    Linux*)
      OS="Linux"
      GREP="grep"
      SED="sed"
      MD5SUM="md5sum"
      MD5COL=1
      ;;
    SunOS*)
      OS="SunOS"
      GREP="/usr/xpg4/bin/grep"
      SED="/usr/xpg4/bin/sed"
      MD5SUM="digest -a md5"
      MD5COL=1
      ;;
    AIX*)
      OS="AIX"
      GREP="grep"
      SED="sed"
      MD5SUM="md5sum"
      MD5COL=1
      ;;
    HP-UX*)
      OS="HP-UX"
      GREP="grep"
      SED="sed"
      if [ -f /usr/local/bin/md5 ]; then
        MD5SUM="/usr/local/bin/md5"
        MD5COL=4
      else
        MD5SUM="md5sum"
        MD5COL=1
      fi
      ;;
    *)
      OS="Unknown"
      GREP="grep"
      SED="sed"
      MD5SUM="md5sum"
      MD5COL=1
      ;;
  esac

  # Export for use in other scripts
  export OS GREP SED MD5SUM MD5COL
}

# Setup directories
setup_directories() {
  local base_dir="$1"

  # Define directory structure
  readonly SCRIPT_DIR="$base_dir"
  readonly OUTPUT_DIR="$SCRIPT_DIR/output"
  readonly LOG_DIR="$SCRIPT_DIR/log"
  readonly SQL_DIR="$SCRIPT_DIR/sql"
  readonly TMP_DIR="$SCRIPT_DIR/tmp"

  # Create directories if they don't exist
  for dir in "$OUTPUT_DIR" "$LOG_DIR" "$TMP_DIR"; do
    [ ! -d "$dir" ] && mkdir -p "$dir"
  done

  # Export for use in other scripts
  export SCRIPT_DIR OUTPUT_DIR LOG_DIR SQL_DIR TMP_DIR
}

# Logging functions with color support
log_info() {
  local green=""
  local reset=""
  # Only use colors if terminal supports it and we're not redirecting
  if [ -t 1 ] && tput colors >/dev/null 2>&1; then
    green=$(tput setaf 2)
    reset=$(tput sgr0)
  fi
  echo "${green}[INFO]${reset} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
  local red=""
  local reset=""
  if [ -t 2 ] && tput colors >/dev/null 2>&1; then
    red=$(tput setaf 1)
    reset=$(tput sgr0)
  fi
  echo "${red}[ERROR]${reset} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_warning() {
  local yellow=""
  local reset=""
  if [ -t 2 ] && tput colors >/dev/null 2>&1; then
    yellow=$(tput setaf 3)
    reset=$(tput sgr0)
  fi
  echo "${yellow}[WARNING]${reset} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

# Progress indicator
show_progress() {
  local msg="$1"
  local progress_char="${2:-.}"
  echo -n "$msg"
  while true; do
    echo -n "$progress_char"
    sleep 1
  done
}

# Check required commands
check_requirements() {
  local missing_commands=()

  for cmd in $REQUIRED_COMMANDS; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      missing_commands+=("$cmd")
    fi
  done

  if [ ${#missing_commands[@]} -ne 0 ]; then
    log_error "Missing required commands: ${missing_commands[*]}"
    log_error "Please install the missing commands and try again"
    return 1
  fi

  return 0
}

# Set up locale
setup_locale() {
  local current_locale
  current_locale=$(echo "$LANG" | cut -d '.' -f 1)
  export LANG=C
  export LANG="${current_locale}.UTF-8"
}

# Compression utility detection with fallback options
detect_compression() {
  # Try zip first (preferred for wider compatibility)
  if command -v zip >/dev/null 2>&1; then
    COMPRESS_CMD="zip"
    COMPRESS_EXT="zip"
    COMPRESS_OPTS="-q"
  # Then try gzip
  elif command -v gzip >/dev/null 2>&1; then
    COMPRESS_CMD="gzip"
    COMPRESS_EXT="tar.gz"
    COMPRESS_OPTS="-9"
  # Finally try compress
  elif command -v compress >/dev/null 2>&1; then
    COMPRESS_CMD="compress"
    COMPRESS_EXT="tar.Z"
    COMPRESS_OPTS=""
  else
    log_error "No compression utility found. Please install zip, gzip, or compress."
    return 1
  fi

  export COMPRESS_CMD COMPRESS_EXT COMPRESS_OPTS
}

# Clean up function with error handling
cleanup() {
  local exit_code=$?
  log_info "Cleaning up temporary files..."

  # Kill any background progress indicators
  kill $(jobs -p) 2>/dev/null || true

  # Remove temporary files
  if [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"/* || log_warning "Failed to clean up some temporary files"
  fi

  # Restore terminal settings if needed
  tput cnorm 2>/dev/null || true

  return $exit_code
}

# Enhanced error handler with more detailed reporting
error_handler() {
  local line_no=$1
  local error_code=$2
  local command="${3:-unknown}"

  log_error "==============================================="
  log_error "Error occurred in script at line: $line_no"
  log_error "Command: $command"
  log_error "Exit code: $error_code"
  log_error "OS: $OS"
  log_error "Shell: $SHELL"
  log_error "==============================================="

  cleanup
  exit "$error_code"
}

# Set up error handling
trap 'error_handler ${LINENO} $? "${BASH_COMMAND}"' ERR
trap cleanup EXIT

# Initialize environment with progress indication
init_environment() {
  show_progress "Initializing environment " &
  progress_pid=$!

  detect_os
  setup_locale
  detect_compression
  check_requirements

  kill $progress_pid
  wait $progress_pid 2>/dev/null || true
  echo " done"
}

# Utility function to format file sizes
format_size() {
  local size=$1
  local scale=1
  local suffix="B"

  if [ "$size" -gt $((1024 * 1024 * 1024)) ]; then
    size=$((size / (1024 * 1024 * 1024)))
    suffix="GB"
  elif [ "$size" -gt $((1024 * 1024)) ]; then
    size=$((size / (1024 * 1024)))
    suffix="MB"
  elif [ "$size" -gt 1024 ]; then
    size=$((size / 1024))
    suffix="KB"
  fi

  echo "${size}${suffix}"
}
