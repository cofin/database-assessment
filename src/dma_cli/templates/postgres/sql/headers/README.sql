/*
PostgreSQL Collection Script Headers

These files provide consistent CSV headers for cases where queries return no data.
This ensures that downstream processing tools can still parse the output files
correctly, even when tables are empty or objects don't exist.

Usage:
- Headers are automatically applied by the collection script
- Each .header file corresponds to a .sql collection script
- Format matches the SELECT column list in the corresponding query
*/
