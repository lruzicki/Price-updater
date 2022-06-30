from turtle import update
import mysql.connector
import requests
from select import select
import pandas as pd
import openpyxl
import logging
import schedule
import time

class SchedulerSetUp:

    def __init__(self, label=None):
        self.mydb = None
        self.mycursor = None
        self.logger = None
        self.result = None

    #Creating and Configuring Logger
    def startLogger(self):
        Log_Format = "%(levelname)s %(asctime)s - %(message)s"

        logging.basicConfig(filename = "logfile.log",
                            filemode = "a",
                            format = Log_Format, 
                            level = logging.ERROR)
        
        self.logger = logging.getLogger()

    def connectToDB(self):
        try:
            self.mydb = mysql.connector.connect(host = "localhost", user = "root", passwd = "root")
        except:
            self.logger.error("Cannot connect to database!")

    def getAllProducts(self):
        #get all product and put them in var
        self.mycursor = self.mydb.cursor()

        self.mycursor.execute("select * FROM `mydb`.`Product`")

        self.result = self.mycursor.fetchall()
    
    def addColumndsTomydb(self):
        # add coulumns to database
        try:
            self.mycursor.execute("ALTER TABLE `mydb`.`Product` ADD `UnitPriceUSD` DECIMAL")
        except:
            print("UnitPriceUSD already exists")
        try:
            self.mycursor.execute("ALTER TABLE `mydb`.`Product` ADD `UnitPriceEURO` DECIMAL")
        except:
            print("UnitPriceEURO already exists")
    
    def updatePrices(self, current_usd_exchange, current_euro_exchange):
        # add foreign currency prices to mydb
        all_products = self.mycursor.fetchall()
        for iterate_product in self.result:
            foreign_currency_prices = (float(iterate_product[6]) / current_euro_exchange, float(iterate_product[6]) / current_usd_exchange, iterate_product[0])
            self.mycursor.execute("UPDATE `mydb`.`Product` SET `UnitPriceEURO` = %s, `UnitPriceUSD` = %s WHERE `ProductID` = %s", foreign_currency_prices)

        self.mydb.commit()
        self.logger.error("UnitPriceEURO and UnitPriceUSD updated")

    
    def getDataFromNBPAPI(self):
        response = requests.get("http://api.nbp.pl/api/exchangerates/tables/a/")
        if response.status_code != 200:
            self.logger.error("NBP API dosen't respond! Prices not updated!")

        # take data from json file
        exchange_info = response.json()
        for i in exchange_info[0]['rates']:
            if i['code'] == 'EUR':
                current_euro_exchange = i['mid']
            if i['code'] == 'USD':
                current_usd_exchange = i['mid'] 
        
        self.updatePrices(current_euro_exchange, current_usd_exchange)
    
    def importToExcel(self, filename = 'products.xlsx'):
        self.startScheduler()
        # prepare data to import mydb to dataframe and excel file
        self.mycursor.execute("SHOW COLUMNS FROM `mydb`.`Product`;")
        result = self.mycursor.fetchall()
        column_names = []
        column_index = []
        # set column order to match the client require order
        for i in range(11):
            column_index.append(i)
            if i == 6:
                column_index += ([12, 13])
        for i in column_index:
            column_names.append(result[i][0])

        # make empty dataframe with coulmn names from mydb
        df = pd.DataFrame(columns = column_names)

        product_data = []
        self.mycursor.execute("select * FROM `mydb`.`Product`")
        result = self.mycursor.fetchall()

        # make dict with pairs column name: value in client order
        for product in result:
            dict = {column_names[i]: product[column_index[i]] for i in range(len(column_index))}
            df = df.append(dict, ignore_index = True)

        # import dataframe to excel file
        df.to_excel(filename)

    def startScheduler(self):
        self.connectToDB()
        self.startLogger()
        self.addColumndsTomydb()
        self.getAllProducts()
        self.getDataFromNBPAPI()
