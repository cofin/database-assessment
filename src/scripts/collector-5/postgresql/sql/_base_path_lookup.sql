/*
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
*/

-- Determine which SQL path to use based on version
WITH version_info AS (
  SELECT
    current_setting('server_version') as full_version,
    substring(current_setting('server_version') from '^[0-9]+\.?[0-9]*') as major_version,
    substring(current_setting('server_version') from '^[0-9]+') as major_num
)
SELECT
  CASE
    WHEN major_version = '9.6' THEN '9.6'
    WHEN major_num::int >= 10 AND major_num::int <= 16 THEN major_num::text
    ELSE 'base'
  END as sql_path
FROM version_info;
