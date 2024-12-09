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

# PostgreSQL specific constants
readonly PG_REQUIRED_COMMANDS="psql pg_isready"
readonly PG_DEFAULT_PORT=5432
readonly PG_APP_NAME="google-db-assessment-collector"
readonly PG_MIN_VERSION="9.6"
readonly PG_MAX_VERSION="16"

# PostgreSQL specific logging
pg_log() {
    local level=$1
    shift
    local msg="[POSTGRES-$level] $(date '+%Y-%m-%d %H:%M:%S') - $*"
    case "$level" in
        ERROR)   echo "$msg" >&2 ;;
        WARNING) echo "$msg" >&2 ;;
        INFO)    echo "$msg" ;;
        DEBUG)   [[ ${PG_DEBUG:-0} -eq 1 ]] && echo "$msg" ;;
    esac
}

# PostgreSQL connection handling
pg_build_connection_string() {
    local user="$1"
    local pass="$2"
    local host="$3"
    local port="$4"
    local dbname="$5"

    # Validate required parameters
    [[ -z "$user" || -z "$host" || -z "$dbname" ]] && {
        pg_log ERROR "Missing required connection parameters"
        return 1
    }

    # Set defaults
    port=${port:-$PG_DEFAULT_PORT}

    # Set password in environment for security
    export PGPASSWORD="$pass"
    export PGAPPNAME="$PG_APP_NAME"

    # Return connection string
    echo "postgresql://$user@$host:$port/$dbname"
}

# PostgreSQL version handling
pg_get_version() {
    local connstr="$1"
    local version_query="SELECT version(),
                               current_setting('server_version_num')::integer as version_num,
                               current_setting('server_version') as version_str"

    psql "$connstr" -t -A -c "$version_query" 2>/dev/null || {
        pg_log ERROR "Failed to get PostgreSQL version"
        return 1
    }
}

pg_check_version_compatibility() {
    local version_num="$1"

    # Convert version to numeric format (e.g., 90600 for 9.6)
    local min_version_num=90600
    local max_version_num=160000

    if [[ $version_num -lt $min_version_num ]]; then
        pg_log ERROR "PostgreSQL version too old. Minimum supported version is $PG_MIN_VERSION"
        return 1
    elif [[ $version_num -gt $max_version_num ]]; then
        pg_log WARNING "PostgreSQL version $version_num may not be fully supported"
    fi

    return 0
}

# Query execution with error handling
pg_execute_query() {
    local connstr="$1"
    local query="$2"
    local output_file="$3"
    local options="${4:--A -t}"  # Default to unaligned, tuples only
    local error_file="${5:-/dev/null}"

    # Execute query with timeout and error handling
    if ! PGCONNECT_TIMEOUT=10 psql "$connstr" $options -v ON_ERROR_STOP=1 \
         -f "$query" > "$output_file" 2>"$error_file"; then
        pg_log ERROR "Query execution failed: $(cat "$error_file")"
        return 1
    fi

    # Check if output was generated
    if [[ ! -s "$output_file" ]]; then
        pg_log WARNING "Query produced no output: $query"
    fi

    return 0
}

# Connection testing with detailed diagnostics
pg_test_connection() {
    local host="$1"
    local port="$2"
    local user="$3"
    local dbname="$4"

    pg_log INFO "Testing connection to PostgreSQL server $host:$port..."

    # Test basic connectivity
    if ! pg_isready -h "$host" -p "$port" -U "$user" -d "$dbname" -t 10 >/dev/null 2>&1; then
        pg_log ERROR "Failed to connect to PostgreSQL server"
        pg_log ERROR "Please check:"
        pg_log ERROR "  - Server is running and accepting connections"
        pg_log ERROR "  - Network connectivity to $host:$port"
        pg_log ERROR "  - PostgreSQL client authentication configuration"
        return 1
    fi

    # Test permissions
    local perm_query="SELECT current_user, current_database(),
                            has_database_privilege(current_user, 'pg_read_all_settings') as can_read_settings,
                            has_database_privilege(current_user, current_database(), 'CONNECT') as can_connect"

    local perm_check
    perm_check=$(PGPASSWORD="$PGPASSWORD" psql -h "$host" -p "$port" -U "$user" -d "$dbname" \
                     -t -A -c "$perm_query" 2>/dev/null)

    if [[ $? -ne 0 ]]; then
        pg_log ERROR "Failed to verify user permissions"
        return 1
    fi

    pg_log INFO "Successfully connected to PostgreSQL server"
    return 0
}
