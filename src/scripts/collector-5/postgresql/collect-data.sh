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

# Source PostgreSQL functions
# shellcheck source=./lib/postgresql.sh
. "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
. "$(dirname "${BASH_SOURCE[0]}")/lib/postgresql.sh"

# Print usage information
print_usage() {
  cat << EOF
Database Migration Assessment PostgreSQL Data Collector

Usage:
  $0 [OPTIONS]

Connection Options (required):
  --connectionStr         Connection string formatted as {user}/{password}@//{host}:{port}/{dbname}
  or
  --collectionUserName    Database user name
  --collectionUserPass    Database password
  --hostName             Database server host name
  --port                 Database listener port
  --databaseName         Database name to connect to

Additional Options:
  --manualUniqueId       Optional identifier for this collection
  --vmUserName           Username for SSH session to collect machine information
  --extraSSHArg          Extra SSH arguments (can be specified multiple times)
  --help                 Show this help message

Examples:
  $0 --connectionStr user/pass@//localhost:5432/postgres

  $0 --collectionUserName user --collectionUserPass pass --hostName localhost \\
     --port 5432 --databaseName postgres

EOF
}

# Parse and validate arguments
parse_connection_args() {
  declare -A args
  parse_args args "$@"

  # Check for connection string format
  if [ -n "${args[connectionStr]:-}" ]; then
    # Parse connection string
    local conn="${args[connectionStr]}"
    USER=$(echo "$conn" | cut -d'/' -f1)
    PASS=$(echo "$conn" | cut -d'/' -f2 | cut -d'@' -f1)
    HOST=$(echo "$conn" | cut -d'/' -f4 | cut -d':' -f1)
    PORT=$(echo "$conn" | cut -d':' -f2 | cut -d'/' -f1)
    DBNAME=$(echo "$conn" | cut -d'/' -f5)
  else
    # Check individual parameters
    USER="${args[collectionUserName]:-}"
    PASS="${args[collectionUserPass]:-}"
    HOST="${args[hostName]:-}"
    PORT="${args[port]:-}"
    DBNAME="${args[databaseName]:-}"

    if [ -z "$USER" ] || [ -z "$PASS" ] || [ -z "$HOST" ] || [ -z "$PORT" ] || [ -z "$DBNAME" ]; then
      log_error "Missing required connection parameters"
      print_usage
      exit 1
    fi
  fi

  # Store additional parameters
  MANUAL_ID="${args[manualUniqueId]:-NA}"
  VM_USER="${args[vmUserName]:-}"

  # Handle multiple SSH arguments
  if [ -n "${args[extraSSHArg]:-}" ]; then
    IFS=' ' read -r -a SSH_ARGS <<< "${args[extraSSHArg]}"
  else
    SSH_ARGS=()
  fi

  export USER PASS HOST PORT DBNAME MANUAL_ID VM_USER SSH_ARGS
}

# Main execution
main() {
  if [ "$1" = "--help" ]; then
    print_usage
    exit 0
  fi

  # Initialize environment
  init_pg_environment

  # Parse arguments
  parse_connection_args "$@"

  # Validate requirements
  validate_pg_requirements "$HOST" "$PORT"

  # Build connection string
  local connstr
  connstr=$(build_connection_string "$HOST" "$PORT" "$DBNAME" "$USER" "$PASS")

  # Test connection
  if ! test_connection "$HOST" "$PORT" "$DBNAME" "$USER"; then
    exit 1
  fi

  # Get PostgreSQL version and create file tag
  local version
  version=$(get_pg_version "$connstr")
  local file_tag="${version}_${HOST}-${PORT}_${DBNAME}_$(date +%y%m%d%H%M%S)"

  # Get source ID
  local source_id
  source_id=$(psql "$connstr" -t -A -f "$SQL_DIR/init.sql")

  # Determine SQL version path
  local version_path
  version_path=$(psql "$connstr" -t -A -f "$SQL_DIR/_base_path_lookup.sql")

  log_info "Starting collection for PostgreSQL $version"
  log_info "Using SQL files from path: $version_path"

  # Process SQL files
  if ! process_sql_files "$connstr" "$version_path" "$file_tag" "$source_id" "$MANUAL_ID"; then
    log_error "Failed to process SQL files"
    exit 1
  fi

  # Collect machine specs if VM user provided
  if [ -n "$VM_USER" ]; then
    local specs_file="$OUTPUT_DIR/opdb__postgresql_machine_specs__${file_tag}.csv"
    if ! ./db-machine-specs.sh "$HOST" "$VM_USER" "$file_tag" "$source_id" "$MANUAL_ID" "$specs_file" "${SSH_ARGS[@]}"; then
      log_warning "Failed to collect machine specifications"
    fi
  fi

  # Create archive
  local archive_name="opdb_postgresql__${file_tag}"
  if [ "$COMPRESS_CMD" = "zip" ]; then
    (cd "$OUTPUT_DIR" && zip $COMPRESS_OPTS "${archive_name}.zip" ./*"${file_tag}"*)
  else
    (cd "$OUTPUT_DIR" && tar cf "${archive_name}.tar" ./*"${file_tag}"* && $COMPRESS_CMD $COMPRESS_OPTS "${archive_name}.tar")
  fi

  log_info "Collection completed successfully"
  log_info "Output archive: $OUTPUT_DIR/${archive_name}.${COMPRESS_EXT}"
}

# Execute main function with all arguments
main "$@"
