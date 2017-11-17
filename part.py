#coding=utf-8
from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config
import sys
import decimal

ctx = decimal.Context()
ctx.prec = 12


def float_to_str(f):
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')


def convert_units(num):
    factors = ["G", "M", "K", "k", "R", "", ".", "m", "u", "n", "p"]
    conversion = {'G': '1000000000', 'M': '1000000', 'K': '1000', 'k': '1000', 'R': '1', '.': '1', '': '1', 'm': '0.001', "u": '0.000001', 'n': '0.000000001', 'p': '0.000000000001'}
    val = ""
    mult = ""

    for i in range(len(num)):
        if num[i] == ".":
            mult = num[i]
        if num[i] in factors:
            mult = num[i]
            val = val + "."
        else:
            if num[i].isdigit():
                val = val + (num[i])
            else:
                print("Invalid multiplier")
                return("0")
                break
    if val.endswith("."):
        val = val[:-1]
    m = float(conversion[mult])
    v = float(val)
    r = float_to_str(m * v)

    r = r.rstrip("0")
    r = r.rstrip(".")
    return(r)


ref = sys.argv[1]

resistors = ["R_1206", "R_0805", "R_0603", "R_0402"]
capacitors = ["C_1206", "C_0805", "C_0603", "C_0402"]
quality = ""
variant = ""



def find_part(part_num):

    dbconfig = read_db_config()
    bean = False
    try:
        conn = MySQLConnection(**dbconfig)
        cursor = conn.cursor()

        if (part_num[:6]) in resistors:
            quality = "Resistance"
            variant = "Resistance Tolerance"
            bean = True
        if (part_num[:6]) in capacitors:
            quality = "Capacitance"
            variant = "Dielectric Characteristic"
            bean = True

        if (bean):
            component = part_num.split('_')

            if (len(component)) <= 2:
                print ("Insufficient parameters (Needs 3 or 4) e.g. R_0805_100K_±5%")
                return ("0")

            c_case = component[1]
            c_value = convert_units(component[2])
            if (len(component)) == 4:
                c_characteristics = component[3]

                #A fully specified bean
                sql = """SELECT P.name, P.description, P.stockLevel, P.internalPartNumber, S.name
                            FROM Part P
                            JOIN PartParameter R ON R.part_id = P.id
                            JOIN StorageLocation S ON  S.id = P.storageLocation_id
                            WHERE
                            (R.name = 'Case/Package' AND R.stringValue='{}') OR
                            (R.name = '{}' AND R.normalizedValue = '{}') OR
                            (R.name = '{}' AND R.stringValue LIKE '%{}')
                            GROUP BY P.id
                            HAVING
                            COUNT(DISTINCT R.name)=3""".format(c_case, quality, c_value, variant, c_characteristics)
            else:

                #A partially specified bean
                sql = """SELECT P.name, P.description, P.stockLevel, P.internalPartNumber, S.name
                            FROM Part P
                            JOIN PartParameter R ON R.part_id = P.id
                            JOIN StorageLocation S ON  S.id = P.storageLocation_id
                            WHERE
                            (R.name = 'Case/Package' AND R.stringValue='{}') OR
                            (R.name = '{}' AND R.normalizedValue = '{}')
                            GROUP BY P.id
                            HAVING
                            COUNT(DISTINCT R.name)=2""".format(c_case, quality, c_value)
        else:
            #A specific part number
            sql = """SELECT P.name, P.description, P.stockLevel, P.internalPartNumber, S.name
                    FROM Part P
                    JOIN StorageLocation S ON  S.id = P.storageLocation_id
                    WHERE P.name LIKE '%{}%'""".format(part_num)

        cursor.execute(sql)
        components = cursor.fetchall()
        n_components = len(components)
        print ("{} component(s) meet the search pattern".format(n_components))

        if components == []:
            print("No components match this pattern")
        else:
            for (name, description, stockLevel, partNum, storageID) in components:
                print()
                print((' {:=<102}').format(""))
                print((" | {:17}| {:80.80}|").format(name, description))
                print((' {:-<102}').format(""))
                print((" | Part ID          | {:80}|").format(partNum))
                print((" | Storage location | {:80}|").format(storageID))
                print((" | {:17}| {:<80}|").format("Stock", stockLevel))
                print((' {:=<102}').format(""))
                print()

    except UnicodeEncodeError as err:
        print(err)

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    find_part(ref)
