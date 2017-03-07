#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Project: Nordic Microalgae. http://nordicmicroalgae.org/
# Author: Arnold Andreasson, info@mellifica.se
# Copyright (c) 2011 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License as follows:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import mysql.connector
import sys
# import string
import codecs
  
def execute(db_host = 'localhost', 
            db_name = 'nordicmicroalgae', 
            db_user = 'root', 
            db_passwd = '',
            delete_db_content = False,
            file_name = '../data_import/taxa_dyntaxa.txt', 
            file_encoding = 'utf16',
            field_separator = '\t', 
            row_delimiter = '\r\n'):
    """ Imports content to the main taxa table. """
    try:
        # Connect to db.
        db = mysql.connector.connect(host = db_host, db = db_name, 
                           user = db_user, passwd = db_passwd,
                           use_unicode = True, charset = 'utf8')
        cursor = db.cursor()
        # Remove all rows in table.
        if delete_db_content == True:
            cursor.execute(""" delete from taxa """) 
        # Open file for reading.
        infile = codecs.open(file_name, mode = 'r', encoding = file_encoding)    
        # Iterate over rows in file.
        for rowindex, row in enumerate(infile):
            if rowindex == 0: # First row is assumed to be the header row.
                # Header: Scientific name    Author    Rank    Parent name
                pass
            else:
                row = list(map(str.strip, row.split(field_separator)))
                # row = list(map(unicode, row))
                #
                scientificname = row[0] # ScientificName
                author = row[1] # Author
                if author == 'NULL':
                    author = ''
                rank = row[2] # Rank
                if scientificname:
                    #
                    try:
                        # Check if already in taxa table.
                        cursor.execute("select count(*) from taxa where name = %s",  
#                                        (str(scientificname), ) )
                                       (scientificname,) )
                        result = cursor.fetchone()
                        rowcount = result[0]
                        #
                        if rowcount == 0:
                            # Add to taxa table.
                            
                            cursor.execute("insert into taxa(name, author, rank) values (%s, %s, %s)",
                                           (scientificname, 
                                            author, # Test: author.replace("'", u'´'),
                                            rank))
                        else:
                            print("ERROR: Taxon already exists. Name: " + scientificname + ".")
                    except mysql.connector.Error as e:
                        print("ERROR: Select or insert to taxa failed. Name: " + scientificname + ".")
                        print("ERROR %d: %s" % (e.args[0], e.args[1]))
        #
        # Add parent_id. Id's are automatically generated by the database, and parent_id must be 
        # searched for in the previously generated taxa table.
        #
        # Restart file and iterate.
        infile.seek(0)            
        for rowindex, row in enumerate(infile):
            if rowindex == 0: # First row is assumed to be the header row.
                # Header: Scientific name    Author    Rank    Parent name
                pass
            else:
                row = list(map(str.strip, row.split(field_separator)))
                # row = list(map(unicode, row))
                #
                scientificname = row[0] # ScientificName
                parentname = row[3] # Parent name
                if scientificname and parentname:
                    # Get id from taxa table for scientific name.
                    taxon_id = 0
                    cursor.execute("select id from taxa where name = %s ",
                                   (scientificname,) ) 
                    result = cursor.fetchone()
                    if result:
                        taxon_id = result[0]
                    else:
                        continue
                    # Get id from taxa table for parent name.
                    parent_id = 0
                    cursor.execute("select id from taxa where name = %s ",
                                   (parentname,) ) 
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]
                    else:
                        continue
                    # Updata taxa table.
                    cursor.execute("update taxa set parent_id = %s where id = %s", 
                                   (str(parent_id), str(taxon_id)))
    #
    except mysql.connector.Error as e:
        print("ERROR: MySQL %d: %s" % (e.args[0], e.args[1]))
        print("ERROR: Script will be terminated.")
        sys.exit(1)
    finally:
        if cursor: cursor.close()
        if db: db.close()
        
        
# Main.
if __name__ == '__main__':
    execute()
    