<a href='https://travis-ci.org/shinken-monitoring/mod-import-mysql'><img src='https://api.travis-ci.org/shinken-monitoring/mod-import-mysql.svg?branch=master' alt='Travis Build'></a>
mod-import-mysql
================

What is it?
-----------

This broker module is made to import configurations to Shinken from a MySQL database. 
All configurations read from the database will be added to those read from the standard flat files.

But be carefull of duplicated names!

You can easily use an existing database, you just have to define the queries to suit your database.


Configuration
--------------
Edit the config in etc to match what you want.
