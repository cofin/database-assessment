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

# Source common functions
# shellcheck source=../../lib/common.sh
. "$(dirname "${BASH_SOURCE[0]}")/../../lib/common.sh"

# PostgreSQL specific constants
readonly PG_REQUIRED_COMMANDS="psql pg_isready"
readonly COLLECTOR_TYPE="postgresql"

# PostgreSQL connection handling
build_connection_string() {
  local host="$1"
  local port="$2"
  local dbname="$3"
  local user="$4"
  local password="$5"

  # Build connection string with password as environment variable
  export PGPASSWORD="$password"
  echo "postgresql://$user@$host:$port/$dbname"
}

test_connection() {
  local host="$1"
  local port="$2"
  local dbname="$3"
  local user="$4"

  log_info "Testing connection to PostgreSQL server $host:$port..."

  if ! pg_isready -h "$host" -p "$port" -U "$user" >/dev/null 2>&1; then
    log_error "Failed to connect to PostgreSQL server"
    return 1
  fi

  return 0
}

get_pg_version() {
  local connstr="$1"
  local version

  version=$(psql "$connstr" -t -A -c "SELECT version()")
  if [ $? -ne 0 ]; then
    log_error "Failed to get PostgreSQL version"
    return 1
  fi

  echo "$version"
  return 0
}

execute_query() {
  local connstr="$1"
  local query="$2"
  local output_file="$3"
  local options="${4:--A -t}"  # Default to unaligned, tuples only

  if ! psql "$connstr" $options -f "$query" > "$output_file" 2>>"$LOG_DIR/postgresql_error.log"; then
    log_error "Failed to execute query: $query"
    return 1
  fi

  return 0
}

process_sql_files() {
  local connstr="$1"
  local version_path="$2"
  local file_tag="$3"
  local source_id="$4"
  local manual_id="${5:-NA}"

  # Process SQL files in order
  for sql_file in "$SQL_DIR"/*.sql "$SQL_DIR/$version_path"/*.sql; do
    [ ! -f "$sql_file" ] && continue

    local base_name
    base_name=$(basename "$sql_file" .sql)

    # Skip special files
    case "$base_name" in
      init|_base_path_lookup|version) continue ;;
    esac

    log_info "Processing $base_name..."

    local output_file="$OUTPUT_DIR/opdb__postgresql_${base_name}__${file_tag}.csv"

    # Set variables for the query
    export DMA_SOURCE_ID="$source_id"
    export DMA_MANUAL_ID="$manual_id"
    export PKEY="$file_tag"

    # Execute query
    if ! execute_query "$connstr" "$sql_file" "$output_file"; then
      log_error "Failed to process $base_name"
      return 1
    fi

    # If output is empty, use header file
    if [ ! -s "$output_file" ] && [ -f "$SQL_DIR/headers/${base_name}.header" ]; then
      cp "$SQL_DIR/headers/${base_name}.header" "$output_file"
    fi
  done

  return 0
}

# Initialize PostgreSQL environment
init_pg_environment() {
  init_environment "$COLLECTOR_TYPE" "$PG_REQUIRED_COMMANDS"

  # Additional PostgreSQL-specific initialization can go here
  if [ -z "${PGAPPNAME:-}" ]; then
    export PGAPPNAME="google-db-assessment-collector"
  fi
}

# Validate PostgreSQL specific requirements
validate_pg_requirements() {
  local host="$1"
  local port="$2"

  # Check if port is valid
  if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
    log_error "Invalid port number: $port"
    return 1
  fi

  # Check if host is reachable
  if ! ping -c 1 "$host" >/dev/null 2>&1; then
    log_warning "Host $host may not be reachable"
  fi

  return 0
}
