# Scape information from https://www.barnesandnoble.com/w/effective-python-brett-slatkin/1130203296?ean=9780134853987
#Steps:
#1. Request the webpage from Barnes and Noble
#2. Parse the webpage, select the Product Details section
#3. Extract the product information by iterating through the HTML tags and collecting the text
#3. Save the data as a dictionary
#4  Create a postgresql database
#5. Create a table in the database
#6. Insert the data into the table
#7. Close the database




import bs4
import psycopg2
import re 

#import file instead of url
filename = "Effective_Python.html"

try:
    with open(filename, "r", encoding="utf8") as f:
        html = f.read()
except FileNotFoundError:
    print("File not found. Please check the filename and path.")
    exit()

#turn the html into a soup object
soup = bs4.BeautifulSoup(html, "html.parser")

#find all the necessary tags and data
productDetailsTab = soup.find(id="ProductDetailsTab")

tableHead = productDetailsTab.find_all("th")
tableData = productDetailsTab.find_all("td")

#Create a dictionary to store the data
productInfo = {}
for i in range(len(tableHead)):
    productInfo[tableHead[i].text.replace(":", "")] = tableData[i].text
    


#seperate Product dimentions from the productInfo dictionary into a new dictionary called productDimensions 
productDimensions = {}
for key, value in productInfo.items():
    if "Product dimensions" in key:
        productDimensions[key] = value
print(productDimensions)


#Get the price from the soup and put it in the dictionary
price = soup.find(id="pdp-cur-price").get_text()
price = float(price.replace("$", ""))
productInfo["Price"] = price



pd = productDimensions["Product dimensions"]

#get only the product dimensions from the productDimensions dictionary
patternToRemove = "[(whdx)]"
pd = re.sub(patternToRemove, "", pd)
pd = pd.strip()
pd = pd.split(" ")



# print(pd)
productDimensions = {"Product width": float(pd[0]), "Product height": float(pd[2]), "Product depth": float(pd[4])}
# print(productDimensions)

#combine the two dictionaries into a single dictionary
productInfo.update(productDimensions)

#Clean up unnecessary keys
productInfo.pop("Product dimensions")

print(productInfo)



# Connect to the database and create a cursor
try:
    conn = psycopg2.connect(user="postgres",
                            password="admin",

                            host="localhost",
                            port="5432")
    print("Database connection established")
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL: ", error)
    exit()


#Create a sql query using the dictionary to create a table
sql_query_create = """CREATE TABLE IF NOT EXISTS product_info(
    id SERIAL PRIMARY KEY,
    ISBN13 VARCHAR(13) NOT NULL,
    Publisher VARCHAR(50) NOT NULL,
    Publication_Date DATE NOT NULL,
    Series VARCHAR(50) NOT NULL,
    Edition_Desc VARCHAR(50) NOT NULL,
    Pages INT NOT NULL,
    Sales_Rank INT NOT NULL,
    ProductWidth DECIMAL(5,2) NOT NULL,
    ProductHeight DECIMAL(5,2) NOT NULL,
    ProductDepth DECIMAL(5,2) NOT NULL,
    Price DECIMAL(7,2) NOT NULL
    );
"""

sql_query_insert = "INSERT INTO product_info(ISBN13, Publisher, Publication_Date, Series, Edition_Desc, Pages, Sales_Rank, ProductWidth, ProductHeight, ProductDepth, Price) VALUES (%s, %s, TO_DATE(%s, 'MM/D/YYYY'), %s, %s, %s, %s, %s::DECIMAL, %s::DECIMAL, %s::DECIMAL, %s::DECIMAL);"
values = (productInfo["ISBN-13"], productInfo["Publisher"], productInfo["Publication date"], productInfo["Series"], productInfo["Edition description"], int(productInfo["Pages"]), productInfo["Sales rank"].replace(",", ""), productInfo["Product width"], productInfo["Product height"], productInfo["Product depth"], productInfo["Price"])


#Create the table

with conn.cursor() as cursor:
    cursor.execute(sql_query_create)
    conn.commit()
    print("Table created successfully in PostgreSQL ")

    cursor.execute(sql_query_insert, values)
    conn.commit()
    print("Record inserted successfully into PostgreSQL ")



#Commit the changes to the database
conn.commit()
conn.close()
