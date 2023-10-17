SELECT /*+ MAX_EXECUTION_TIME(5000) */ S.table_schema,
                                       S.table_name,
                                       S.column_name,
                                       T.ENGINE AS storage_engine
                                , concat(char(39), @DMASOURCEID, char(39)) as DMA_SOURCE_ID, concat(char(39), @DMAMANUALID, char(39)) as DMA_MANUAL_ID
FROM information_schema.STATISTICS S
JOIN information_schema.TABLES T ON S.TABLE_SCHEMA=T.TABLE_SCHEMA
AND S.TABLE_NAME = T.TABLE_NAME
WHERE index_type = 'FULLTEXT'
  AND S.table_schema NOT IN ('mysql',
                             'information_schema',
                             'performance_schema',
                             'sys')
;