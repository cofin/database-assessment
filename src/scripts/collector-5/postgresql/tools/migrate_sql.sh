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
. "$(dirname "${BASH_SOURCE[0]}")/../lib/postgresql.sh"

OLD_SQL_DIR="../../../collector/postgres/sql"
NEW_SQL_DIR="../sql"

# Create version-specific directories if they don't exist
for version in base 9.6 {10..16}; do
  mkdir -p "$NEW_SQL_DIR/$version"
done

# Copy and categorize SQL files
for sql_file in "$OLD_SQL_DIR"/*.sql; do
  base_name=$(basename "$sql_file")

  # Skip special files
  case "$base_name" in
    init.sql|_base_path_lookup.sql|version.sql)
      cp "$sql_file" "$NEW_SQL_DIR/"
      continue
      ;;
  esac

  # Check for version-specific markers in the SQL
  if grep -q "version_num.*>=.*90600" "$sql_file"; then
    cp "$sql_file" "$NEW_SQL_DIR/9.6/"
  elif grep -q "version_num.*>=.*100000" "$sql_file"; then
    cp "$sql_file" "$NEW_SQL_DIR/10/"
  else
    cp "$sql_file" "$NEW_SQL_DIR/base/"
  fi
done

# Copy header files
mkdir -p "$NEW_SQL_DIR/headers"
if [ -d "$OLD_SQL_DIR/headers" ]; then
  cp "$OLD_SQL_DIR/headers"/*.header "$NEW_SQL_DIR/headers/"
fi

log_info "SQL files migration completed"
log_info "Please review the categorization of files in $NEW_SQL_DIR"
