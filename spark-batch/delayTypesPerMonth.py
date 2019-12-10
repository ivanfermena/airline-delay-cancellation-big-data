from __future__ import division
from pyspark import SparkConf, SparkContext
from pyspark.sql import *
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql import Row
from datetime import date
import string

conf = SparkConf().setMaster('local[4]').setAppName('airports5')
sc = SparkContext(conf = conf)
sqlContext = SQLContext(sc)

df = sqlContext.read.load("2009-2018.csv", 
                          format='com.databricks.spark.csv', 
                          header='true', 
                          inferSchema='true')

df.registerTempTable("df")

dfA = sqlContext.sql("""
    SELECT YEAR(FL_DATE) as Year, MONTH(FL_DATE) as Month, COUNT(CARRIER_DELAY) as Airline_Delay
    FROM df
    WHERE CARRIER_DELAY > 0.0
    GROUP BY YEAR(FL_DATE), MONTH(FL_DATE)
    ORDER BY Year DESC
""")

dfW = sqlContext.sql("""
    SELECT YEAR(FL_DATE) as Year, MONTH(FL_DATE) as Month, COUNT(WEATHER_DELAY) as Weather_delay
    FROM df
    WHERE WEATHER_DELAY > 0.0
    GROUP BY YEAR(FL_DATE), MONTH(FL_DATE)
    ORDER BY Year DESC
""")

dfN = sqlContext.sql("""
    SELECT YEAR(FL_DATE) as Year, MONTH(FL_DATE) as Month, COUNT(NAS_DELAY) as Air_system_delay
    FROM df
    WHERE NAS_DELAY > 0.0
    GROUP BY YEAR(FL_DATE), MONTH(FL_DATE)
    ORDER BY Year DESC
""")

dfS = sqlContext.sql("""
    SELECT YEAR(FL_DATE) as Year, MONTH(FL_DATE) as Month, COUNT(LATE_AIRCRAFT_DELAY) as Security_delay
    FROM df
    WHERE LATE_AIRCRAFT_DELAY > 0.0
    GROUP BY YEAR(FL_DATE), MONTH(FL_DATE)
    ORDER BY Year DESC
""")

partial1 = dfA.join(dfW,['Year', 'Month'],"outer")
partial2 = partial1.join(dfN,['Year', 'Month'],"outer")
partial3 = partial2.join(dfS,['Year', 'Month'],"outer")


semi_results = partial3.rdd.map(lambda x: (x[0], x[1], x[2], x[3], x[4], x[5], x[2] + x[3] + x[4] + x[5]))
results = semi_results.map(lambda x: (x[0], x[1], "{:12.2f}".format((x[2]/x[6]) * 100),"{:12.2f}".format((x[3]/x[6]) * 100), "{:12.2f}".format((x[4]/x[6]) * 100), "{:12.2f}".format((x[5]/x[6]) * 100)))
results.toDF(["Year", "Month", "Airline_Delay", "Weather_delay", "Air_system_delay", "Security_delay"]).show()
#results.toDF(["Year", "Month", "Airline_Delay", "Weather_delay", "Air_system_delay", "Security_delay"]).repartition(1).write.format('com.databricks.spark.csv').option("header", "true").save("delayTypePerMonth")
