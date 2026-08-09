# Databricks notebook source
# DBTITLE 1,Imports
import pyspark.sql.functions as F

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'ff')
dbutils.widgets.text('SCHEMA', 'ud')
dbutils.widgets.text('READ_TABLE', 'bbm_drafts')

# COMMAND ----------

# DBTITLE 1,Get widget values
CATALOG = dbutils.widgets.get('CATALOG') # ff
SCHEMA = dbutils.widgets.get('SCHEMA') # ud
READ_TABLE = dbutils.widgets.get('READ_TABLE') # bbm_drafts

# COMMAND ----------

# DBTITLE 1,Load data
sdf = spark.table(f'{CATALOG}.{SCHEMA}.{READ_TABLE}')

# COMMAND ----------

# DBTITLE 1,Preview
display(sdf.limit(25))

# COMMAND ----------

# DBTITLE 1,ADP analysis
adp = (
    sdf
    .withColumn('y', F.year(F.to_date('draft_time')))
    .withColumn('overall_pick_number', F.col('overall_pick_number').try_cast('int'))
    .withColumn('projection_adp', F.col('projection_adp').try_cast('double'))
    .groupBy('player_name', 'position_name', 'y', 'pick_points')
    .agg(
        F.min('overall_pick_number').alias('min_pick'),
        F.avg('projection_adp').alias('adp'),
        F.max('overall_pick_number').alias('max_pick'),
        F.stddev_pop('overall_pick_number').alias('sd_pick')
    )
    .select('y', 'position_name', 'adp', 'min_pick', 'max_pick', 'sd_pick')
)

# COMMAND ----------

# DBTITLE 1,Display ADP
display(adp)