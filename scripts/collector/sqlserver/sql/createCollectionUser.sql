/*
Copyright 2023 Google LLC

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

SET NOCOUNT ON;
SET LANGUAGE us_english;

DECLARE @dbname VARCHAR(50);
DECLARE @COLLECTION_USER VARCHAR(256);
DECLARE @COLLECTION_PASS VARCHAR(256);
DECLARE @PRODUCT_VERSION AS INTEGER;
DECLARE @CLOUDTYPE AS VARCHAR(256);

DECLARE db_cursor CURSOR LOCAL FOR
SELECT name
FROM sys.databases
WHERE name NOT IN ('model','msdb','tempdb','distribution','reportserver', 'reportservertempdb','resource','rdsadmin')
    AND state = 0
	AND is_read_only = 0;

SELECT @PRODUCT_VERSION = CONVERT(INTEGER, PARSENAME(CONVERT(NVARCHAR(255), SERVERPROPERTY('productversion')), 4));
SELECT @COLLECTION_USER = N'$(collectionUser)'
SELECT @COLLECTION_PASS = N'$(collectionPass)'
SELECT @CLOUDTYPE = 'NONE';

IF UPPER(@@VERSION) LIKE '%AZURE%'
	SELECT @CLOUDTYPE = 'AZURE'

BEGIN
IF DB_NAME() = 'master'
  IF NOT EXISTS (SELECT name FROM sys.sql_logins WHERE name = @COLLECTION_USER)
	BEGIN TRY
    IF @CLOUDTYPE = 'AZURE'
        exec ('CREATE LOGIN [' + @COLLECTION_USER + '] WITH PASSWORD=N''' + @COLLECTION_PASS + '''');
    ELSE
		exec ('CREATE LOGIN [' + @COLLECTION_USER + '] WITH PASSWORD=N''' + @COLLECTION_PASS + ''', DEFAULT_DATABASE=[master], CHECK_EXPIRATION=OFF, CHECK_POLICY=OFF');
    END TRY
	BEGIN CATCH
        SELECT
        host_name() as host_name,
        db_name() as database_name,
        'Create Login' as module_name,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
    END CATCH
END;

BEGIN
    IF @CLOUDTYPE = 'AZURE'
	BEGIN TRY
        exec ('ALTER SERVER ROLE ##MS_DefinitionReader## ADD MEMBER [' + @COLLECTION_USER + ']');
        exec ('ALTER SERVER ROLE ##MS_SecurityDefinitionReader## ADD MEMBER [' + @COLLECTION_USER + ']');
        exec ('ALTER SERVER ROLE ##MS_ServerStateReader## ADD MEMBER [' + @COLLECTION_USER + ']');
	END TRY
	BEGIN CATCH
        SELECT
        host_name() as host_name,
        db_name() as database_name,
        'Execute SERVER ROLE Grant in ' + DB_NAME() + ' DB' as module_name,
		SUBSTRING(CONVERT(NVARCHAR(255),ERROR_LINE()),1,254) as error_line,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
        SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
	END CATCH
END
BEGIN
    IF @CLOUDTYPE <> 'AZURE'
	BEGIN
		BEGIN TRY
        	exec ('GRANT VIEW SERVER STATE TO [' + @COLLECTION_USER + ']');
        	exec ('GRANT VIEW ANY DATABASE TO [' + @COLLECTION_USER + ']');
        	exec ('GRANT VIEW ANY DEFINITION TO [' + @COLLECTION_USER + ']');
		END TRY
		BEGIN CATCH
			SELECT
				host_name() as host_name,
				db_name() as database_name,
				'Execute Grant in ' + DB_NAME() + ' DB' as module_name,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_LINE()),1,254) as error_line,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
		END CATCH
        IF @PRODUCT_VERSION > 11
		BEGIN TRY
            exec ('GRANT SELECT ALL USER SECURABLES TO [' + @COLLECTION_USER + ']');
		END TRY
		BEGIN CATCH
			SELECT
				host_name() as host_name,
				db_name() as database_name,
				'Execute USER SECURABLE Grant in ' + DB_NAME() + ' DB' as module_name,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_LINE()),1,254) as error_line,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
		END CATCH
		IF @PRODUCT_VERSION > 15
		BEGIN TRY
            exec('GRANT VIEW SERVER PERFORMANCE STATE TO [' + @COLLECTION_USER + ']');
            exec('GRANT VIEW SERVER SECURITY STATE TO [' + @COLLECTION_USER + ']');
            exec('GRANT VIEW ANY PERFORMANCE DEFINITION TO [' + @COLLECTION_USER + ']');
            exec('GRANT VIEW ANY SECURITY DEFINITION TO [' + @COLLECTION_USER + ']');
		END TRY
		BEGIN CATCH
			SELECT
				host_name() as host_name,
				db_name() as database_name,
				'Execute VIEW SERVER Grant in ' + DB_NAME() + ' DB' as module_name,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_LINE()),1,254) as error_line,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
		END CATCH
	END;
END;

IF @CLOUDTYPE = 'AZURE'
BEGIN
  IF NOT EXISTS (SELECT name FROM sys.sysusers WHERE name = @COLLECTION_USER)
	BEGIN TRY
		exec ('CREATE USER [' + @COLLECTION_USER + '] FROM LOGIN [' + @COLLECTION_USER + '] WITH DEFAULT_SCHEMA=dbo');
    END TRY
    BEGIN CATCH
		SELECT
			host_name() as host_name,
			db_name() as database_name,
			'Execute Create User in ' + DB_NAME() + ' DB' as module_name,
			SUBSTRING(CONVERT(NVARCHAR(255),ERROR_LINE()),1,254) as error_line,
			SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
			SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
			SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
			SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
    END CATCH
END;

IF @CLOUDTYPE <> 'AZURE'
BEGIN
    OPEN db_cursor
    FETCH NEXT FROM db_cursor INTO @dbname
    WHILE @@FETCH_STATUS = 0
		BEGIN TRY
        	exec ('
            use [' + @dbname + '];
            IF NOT EXISTS (SELECT [name]
            FROM [sys].[database_principals]
            WHERE [type] = N''S'' AND [name] = N''' + @COLLECTION_USER + ''')
            BEGIN
                CREATE USER [' + @COLLECTION_USER + '] FOR LOGIN  [' + @COLLECTION_USER + '];
            END;
			GRANT VIEW DATABASE STATE TO  [' + @COLLECTION_USER + '];');
		END TRY
		BEGIN CATCH
			SELECT
				host_name() as host_name,
				@dbname as used_db_name,
				db_name() as current_database_name,
				'Execute Grant in ' + DB_NAME() + ' DB' as module_name,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_NUMBER()),1,254) as error_number,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_SEVERITY()),1,254) as error_severity,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_STATE()),1,254) as error_state,
				SUBSTRING(CONVERT(NVARCHAR(255),ERROR_MESSAGE()),1,512) as error_message;
		END CATCH
	FETCH NEXT FROM db_cursor INTO @dbname;
	CLOSE db_cursor
	DEALLOCATE db_cursor
END;
