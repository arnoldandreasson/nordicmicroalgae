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
import codecs
# import string
import json

def execute(file_name = '../data_import/facts.txt', 
            file_encoding = 'utf16',
            field_separator = '\t', 
            row_delimiter = '\r\n',
            db_host = 'localhost', 
            db_name = 'nordicmicroalgae', 
            db_user = 'root', 
            db_passwd = '',
            delete_db_content = False
            ):
    """ Imports facts managed by our own contributors. """
    try:
        # Connect to db.
        db = mysql.connector.connect(host = db_host, db = db_name, 
                           user = db_user, passwd = db_passwd,
                           use_unicode = True, charset = 'utf8')
        cursor=db.cursor()
        # Remove all rows in table.
        if delete_db_content == True:
            cursor.execute(""" delete from taxa_facts """) 
        # Open file for reading.
        infile = codecs.open(file_name, mode = 'r', encoding = file_encoding)    
        # Iterate over rows in file.
        for rowindex, row in enumerate(infile):
            if rowindex == 0: # First row is assumed to be the header row.
                headers = list(map(str.strip, row.split(field_separator)))
                # headers = list(map(unicode, headers))
            else:
                row = list(map(str.strip, row.split(field_separator)))
                # row = list(map(unicode, row))
                # Get taxon_id from name.
                cursor.execute("select id from taxa " + 
                                 "where name = %s", (row[0],) )
                result = cursor.fetchone()
                if result:
                    taxon_id = result[0]
                else:
                    print("Error: Can't find taxon i taxa. Name: " + row[0])
                    continue # Skip this taxon.
                # Get facts_json from db.
                cursor.execute("select facts_json from taxa_facts where taxon_id = %s", 
                               (taxon_id,) )
                result = cursor.fetchone()
                if result:
                    # From string to dictionary.
                    factsdict = json.loads(result[0], encoding = 'utf-8')
                    # Add column values to row, if available.
                    for headeritem in headers:
                        row.append(factsdict.get(headeritem, ''))
                else:
                    # Add empty columns.
                    factsdict = {}
                # Update facts.
                for colindex, headeritem in enumerate(headers):
                    if not headeritem in ['Taxon name', 'Classification']:
                        factsdict[headeritem] = row[colindex]
                # Convert facts to string.
                jsonstring = json.dumps(factsdict, # decoding = 'utf-8', 
                                     sort_keys=True, indent=4)
                # Check if db row exists. 
                cursor.execute("select count(*) from taxa_facts where taxon_id = %s", 
                               (taxon_id,) )
                result = cursor.fetchone()
                if result[0] == 0: 
                    cursor.execute("insert into taxa_facts(taxon_id, facts_json) values (%s, %s)", 
                                   (str(taxon_id), jsonstring))
                else:
                    cursor.execute("update taxa_facts set facts_json = %s where taxon_id = %s", 
                                   (jsonstring, str(taxon_id)))
    #
    except (IOError, OSError):
        print("ERROR: Can't read text file." + infile)
        print("ERROR: Script will be terminated.")
        sys.exit(1)
    except mysql.connector.Error as e:
        print("ERROR: MySQL %d: %s" % (e.args[0], e.args[1]))
        print("ERROR: Script will be terminated.")
        sys.exit(1)
    finally:
        if db: db.close()
        if cursor: cursor.close()
        if infile: infile.close() 


# Main.
if __name__ == '__main__':
    execute()