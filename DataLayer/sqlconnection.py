# -*- coding: utf-8 -*-
import logging

import requests
import pyodbc
import json
import re

connectionString = (r'Driver={SQL Server};'
                    r'Server=DESKTOP-G22L933\SQLEXPRESS;'
                    r'Database=OcD;'
                    r'Trusted_Connection=yes;')
log = logging.getLogger("server")
logging.basicConfig(level=logging.DEBUG)

def getNumberOfMatchingNames(names):
    result = list()
    conn = pyodbc.connect(connectionString)
    cursor = conn.cursor()
    sql = '''SELECT DISTINCT prodName FROM oCd.dbo.PRODUCTS'''
    cursor.execute(sql)

    for row in cursor:
        result.append(row[0])

    return len(set(names) & set(result))


def getAllProducts():
    conn = pyodbc.connect(connectionString)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oCd.dbo.PRODUCTS')
    for row in cursor:
        print(row)


def getProductByName(name):
    conn = pyodbc.connect(connectionString)
    cursor = conn.cursor()
    sql = '''SELECT * FROM oCd.dbo.PRODUCTS WHERE  prodName LIKE (?)'''
    cursor.execute(sql, '%' + name + '%')
    if cursor.rowcount is 0:
        return None
    return cursor


def getProductByBarcode(barcode):
    conn = pyodbc.connect(connectionString)
    cursor = conn.cursor()
    sql = '''SELECT * FROM oCd.dbo.PRODUCTS WHERE  barcode = (?)'''
    cursor.execute(sql, barcode)
    if cursor.rowcount is 0:
        return None
    return cursor


def insertProduct(barcode, name, quantity):
    conn = pyodbc.connect(connectionString)

    cursor = conn.cursor()
    sql = '''
                    INSERT INTO oCd.dbo.PRODUCTS (barcode, prodName, quantity)
                    VALUES
                    (?,?,?)'''

    params = (barcode, name, quantity)
    cursor.execute(sql, params)
    conn.commit()


def getNameFromAPI(barcode):
    headers = {"api_key": "d7a7986c35e4c4a3b64b96f2accb0ace2ce5f7a1", "action": "GetProductsByBarCode",
            "product_barcode": barcode}
    response = requests.post('https://api.superget.co.il/', headers)
    response_text = json.loads(response.text)
    try:
        name = response_text[0]["product_name"]
        return name
    except KeyError as exc:
        log.error("Exception occured :  {} ".format(exc))
        return None


def getNameFromDB(barcode):
    name = ''
    conn = pyodbc.connect(connectionString)
    cursor = conn.cursor()
    sql = '''SELECT prodname FROM oCd.dbo.PRODUCTS WHERE  barcode = (?)'''
    cursor.execute(sql, barcode)
    if cursor.rowcount is 0:
        return None
    for row in cursor:
        name = name + row[0]
    return name


def parseName(name):
    prodName = ''
    quantity = 0 # DOR : unused -  can remove
    details = re.split(r'(\d+)', name)
    if len(details) > 3:
        if '*' in details:  # deal packeges
            index = details.index('*')
            for val in range(index - 1):
                prodName = prodName + details[val] + ' '
            quantity = float(details[index - 1]) * float(details[index + 1])

        else:  # fat precents
            prodName = details[0]
            quantity = float(details[3])

    elif len(details) == 3:  # name + weight + massurement
        prodName = details[0]
        prodName = prodName.replace('-', '')
        quantity = float(details[1])

    else:  # just name
        prodName = name
        quantity = 1.0
    return prodName, quantity


def scanBarcode(barcode):
    prodName = getNameFromDB(barcode)
    if prodName is None:
        prodName = getNameFromAPI(barcode)
        if prodName is not None:
            details = parseName(prodName)
            insertProduct(barcode, details[0], int(details[1]))
            prodName = details[0]
    if prodName is not None:
        return prodName
    else:
        return -1
