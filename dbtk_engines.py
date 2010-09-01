"""Database Toolkit Engines

This module contains Engine class implementations for each supported database 
system. These classes inherit from the dbtk_models.py Engine class and must
also implement the following:

  name -- the name of the database platform
  abbreviation -- an abbreviation used to select the database platform from 
                  the command line
  datatypes -- a list of data types from the database system that correspond to
               generic data types used in the DBTK script, in the following
               order:
               primary key, integer, float, decimal, text, boolean
  required_opts -- a list of sets of required information to establish a 
                   connection, in the following format: 
                   [argument name, prompt, default]
  
In addition, the Engine class implementations may override any method of the
default Engine class.

Importing ALL_ENGINES from this module will give a list of each Engine class
that has been implemented.


"""

from dbtk_models import *

class MySQLEngine(Engine):
    """Engine instance for MySQL."""
    name = "MySQL"
    abbreviation = "m"
    datatypes = ["INT(5) NOT NULL AUTO_INCREMENT", 
                 "INT", 
                 "DOUBLE",
                 "DECIMAL", 
                 "VARCHAR", 
                 "BIT"]
    required_opts = [["username", 
                      "Enter your MySQL username: ", 
                      "root"],
                     ["password", 
                      "Enter your password: ", 
                      ""],
                     ["hostname", 
                      "Enter your MySQL host or press Enter " +
                      "for the default (localhost): ", 
                      "localhost"],                     
                     ["sqlport", 
                      "Enter your MySQL port or press Enter " +
                      "for the default (3306): ", 
                      3306]]
    def insert_data_from_file(self, filename):
        """Calls MySQL "LOAD DATA LOCAL INFILE" statement to perform a bulk 
        insert."""
        if self.table.cleanup.function == no_cleanup:
            print ("Inserting data from " + os.path.basename(filename) 
                   + " . . .")
                
            columns = self.get_insert_columns()            
            statement = """        
LOAD DATA LOCAL INFILE '""" + filename + """'
INTO TABLE """ + self.tablename() + """
FIELDS TERMINATED BY '""" + self.table.delimiter + """'
LINES TERMINATED BY '\\n'
IGNORE """ + str(self.table.header_rows) + """ LINES 
(""" + columns + ")"
            
            self.cursor.execute(statement)
        else:
            return Engine.insert_data_from_file(self, filename)
    def get_cursor(self):
        """Gets the db connection and cursor."""
        import MySQLdb as dbapi
        self.get_input()                
        self.connection = dbapi.connect(host = self.opts["hostname"],
                                        port = int(self.opts["sqlport"]),
                                        user = self.opts["username"],
                                        passwd = self.opts["password"])     
        self.cursor = self.connection.cursor()    


class PostgreSQLEngine(Engine):
    """Engine instance for PostgreSQL."""
    name = "PostgreSQL"
    abbreviation = "p"
    datatypes = ["serial", 
                 "integer", 
                 "double precision",
                 "decimal", 
                 "varchar", 
                 "bit"]    
    required_opts = [["username", 
                      "Enter your PostgreSQL username: ", 
                      "postgres"],
                     ["password", 
                      "Enter your password: ", ""],
                     ["hostname", 
                      "Enter your PostgreSQL host or press Enter " +
                      "for the default (localhost): ", "localhost"],
                     ["sqlport", "Enter your PostgreSQL port or press" + 
                      "Enter for the default (5432): ", 5432],
                     ["database", 
                      "Enter your PostgreSQL database name or press " +
                      "Enter for the default (postgres): ", "postgres"]]            
    def create_db_statement(self):
        """In PostgreSQL, the equivalent of a SQL database is a schema."""
        return Engine.create_db_statement(self).replace("DATABASE", "SCHEMA")
    def create_table(self):
        """PostgreSQL needs to commit operations individually."""
        Engine.create_table(self)
        self.connection.commit()
    def drop_statement(self, objecttype, objectname):
        """In PostgreSQL, the equivalent of a SQL database is a schema."""
        statement = Engine.drop_statement(self, objecttype, objectname) 
        statement += " CASCADE;"
        return statement.replace(" DATABASE ", " SCHEMA ")    
    def insert_data_from_file(self, filename):
        """Use PostgreSQL's "COPY FROM" statement to perform a bulk insert."""
        if ([self.table.cleanup.function, self.table.delimiter, 
             self.table.header_rows] == [no_cleanup, ",", 1]):        
            print ("Inserting data from " + os.path.basename(filename) 
                   + " . . .")
                
            columns = self.get_insert_columns()    
            filename = os.path.abspath(filename)
            statement = """
COPY """ + self.tablename() + " (" + columns + """)
FROM '""" + filename + """'
WITH DELIMITER ','
CSV HEADER"""
            try:
                self.cursor.execute(statement)
                self.connection.commit()
            except:
                self.connection.rollback()
                return Engine.insert_data_from_file(self, filename)
        else:
            return Engine.insert_data_from_file(self, filename)                
    def get_cursor(self):
        """Gets the db connection and cursor."""
        import psycopg2 as dbapi    
        self.get_input()            
        self.connection = dbapi.connect(host = self.opts["hostname"],
                                        port = int(self.opts["sqlport"]),
                                        user = self.opts["username"],
                                        password = self.opts["password"],
                                        database = self.opts["database"])        
        self.cursor = self.connection.cursor()    


class SQLiteEngine(Engine):
    """Engine instance for SQLite."""
    name = "SQLite"
    abbreviation = "s"
    datatypes = ["INTEGER",
                 "INTEGER",
                 "REAL",
                 "REAL",
                 "TEXT",
                 "INTEGER"]
    required_opts = [["database", 
                      "Enter the filename of your SQLite database: ",
                      "sqlite.db"]]
    def create_db(self):
        """SQLite doesn't create databases; each database is a file and needs
        a separate connection."""
        return None
    def tablename(self):
        """The database file is specifically connected to, so database.table 
        is not necessary."""
        return self.table.tablename
    def get_cursor(self):
        """Gets the db connection and cursor."""
        import sqlite3 as dbapi
        self.get_input()
        self.connection = dbapi.connect(self.opts["database"])
        self.cursor = self.connection.cursor()
                

ALL_ENGINES = [MySQLEngine(), PostgreSQLEngine(), SQLiteEngine()]


def choose_engine(opts):
    """Prompts the user to select a database engine"""    
    enginename = opts["engine"]
    
    if not enginename:
        print "Choose a database engine:"
        for engine in ALL_ENGINES:
            if engine.abbreviation:
                abbreviation = "(" + engine.abbreviation + ") "
            else:
                abbreviation = ""
            print "    " + abbreviation + engine.name
        enginename = raw_input(": ")
        enginename = enginename.lower()
    
    engine = Engine()
    if not enginename:
        engine = MySQLEngine()
    else:
        for thisengine in ALL_ENGINES:
            if (enginename == thisengine.name.lower() 
                              or thisengine.abbreviation
                              and enginename == thisengine.abbreviation):
                engine = thisengine
        
    engine.opts = opts
    return engine