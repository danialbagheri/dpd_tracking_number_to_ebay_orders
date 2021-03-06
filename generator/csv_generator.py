import os
import csv
import datetime
import pdb
from ebay import process_ebay_orders
# ups_file = open('ups/ups_tracking_numbers.csv', newline='')

# tracking_numbers = csv.reader(ups_file)
total_processed = 0


def fill_the_empty(row_number):
    '''
    This fills the rows in the shopify orders when a customer have bought more than
    one item. Please check the orders.csv file to understand.
    proobably doesn't do anything at the moment!
    '''
    count = 0
    order_file = open('imports/shopify-orders.csv', newline='')
    orders_reader = csv.reader(order_file)
    previous_row = row_number - 1
    # Here we need to determine how many rows we need to go back.
    import pdb
    pdb.set_trace()
    order_list = list(orders_reader)
    while order_list[previous_row][2] == "":
        previous_row -= 1

    orders = {}
    for order in orders_reader:
        if count == previous_row:
            orders['email'] = order[1]
            orders['status'] = order[4]
            orders['payment_status'] = order[2]
            orders['customer_name'] = order[34]
            orders['address 1'] = order[36]
            orders['address 2'] = order[37]
            orders['company'] = order[38]
            orders['city'] = order[39]
            orders['country'] = order[42]
            orders['post_code'] = order[40].replace(" ", "")
            orders['notes'] = order[44]
            orders['phone'] = order[66]
            orders["status"] = order[4]
        elif count == row_number:
            orders['order_number'] = order[0]
            orders['item_name'] = order[17]
            orders['sku'] = order[20]
            orders['quantity'] = order[16]
            orders['price'] = order[18]
        count += 1
    order_file.close()
    return orders


def process_shopify_orders(file_path=None):
    if file_path:
        path = file_path
    else:
        path = 'imports/shopify-orders.csv'
    message = ""
    parcel_force_orders = []
    ups_orders = []
    box_of_500ml = []
    box_of_200ml = []
    box_of_100ml = []
    box_of_50ml = []
    order_file = open(path, newline='')
    orders_reader = csv.reader(order_file)
    row_count = 0
    col_count = 0
    for row in orders_reader:
        if row_count < 1:
            for col in row:
                # print(f"col {col_count}: row: {col} \n")
                col_count += 1
        if row_count >= 1:
            # pdb.set_trace()
            orders = {}
            quantity = row[16]
            item_name = row[17]
            financial_status = row[2]
            order_number = row[0]
            # customer details needs repeating if financial status is empty
            if financial_status == "":
                orders = fill_the_empty(row_count)
            else:
                orders['status'] = row[4]
                orders['order_number'] = row[0]
                orders['item_name'] = row[17]
                orders['sku'] = row[20]
                orders['quantity'] = row[16]
                orders['email'] = row[1]
                orders['payment_status'] = row[2]
                orders['price'] = row[18]
                orders['customer_name'] = row[34]
                orders['address 1'] = row[36]
                orders['address 2'] = row[37]
                orders['company'] = row[38]
                orders['city'] = row[39]
                orders['country'] = row[42]
                orders['post_code'] = row[40].replace(" ", "")
                orders['notes'] = row[44]
                orders['phone'] = row[66]
                orders["status"] = row[4]

            if quantity:
                try:
                    quantity = int(quantity)
                except:
                    continue
            else:
                quantity = 0

            # northern_ireland = orders['post_code'].lower().startswith('bt')
            if orders['status'] == "unfulfilled" and orders['payment_status'] == "paid" and (orders['sku'] == "5017371155890" or orders['sku'] == "CALB10"):
                if quantity >= 2 and quantity <= 8:
                    for i in range(quantity):
                        ups_orders.append(orders)
                elif quantity == 1:
                    ups_orders.append(orders)
                else:
                    message += f"order number {orders['order_number']} has {quantity} items and must be sent differently. 5litre \n"
                    message += f"Customer name: {orders['customer_name']} phone number: {orders['phone']}\n"
                    message += f"Address: {orders['address 1']}\n {orders['address 2']}\n {orders['post_code']}\n"
            elif orders['status'] == "unfulfilled" and orders['payment_status'] == "paid" and orders['sku'] == "CALB11BOX":
                if quantity >= 2 and quantity <= 8:
                    for i in range(quantity):
                        box_of_500ml.append(orders)
                elif quantity == 1:
                    box_of_500ml.append(orders)
                else:
                    message += f"order number {orders['order_number']} has {quantity} items and must be sent differently. 500ml \n"
            elif orders['status'] == "unfulfilled" and orders['payment_status'] == "paid" and orders['sku'] == "CALB08BOX":

                if quantity >= 2 and quantity <= 8:
                    for i in range(quantity):
                        box_of_200ml.append(orders)

                elif quantity == 1:
                    box_of_200ml.append(orders)
                else:
                    message += f"order number {orders['order_number']} has {quantity} items and must be sent differently. 200ml \n"
            elif orders['status'] == "unfulfilled" and orders['payment_status'] == "paid" and orders['sku'] == "CALB07BOX":

                if quantity >= 2 and quantity <= 8:
                    for i in range(quantity):
                        box_of_100ml.append(orders)

                elif quantity == 1:
                    box_of_100ml.append(orders)
                else:
                    message += f"order number {orders['order_number']} has {quantity} items and must be sent differently. 100ml \n"
            elif orders['status'] == "unfulfilled" and orders['payment_status'] == "paid" and orders['sku'] == "CALB06BOX":

                if quantity >= 2 and quantity <= 8:
                    for i in range(quantity):
                        box_of_50ml.append(orders)

                elif quantity == 1:
                    box_of_50ml.append(orders)
                else:
                    message += f"order number {orders['order_number']} has {quantity} items and must be sent differently. 50ml \n"

            elif orders['status'] == "unfulfilled":
                message += f"order number: {order_number} is to be sent by Royal Mail.\n"
        row_count += 1

    order_file.close()
    return message, parcel_force_orders, ups_orders, box_of_500ml, box_of_200ml, box_of_100ml, box_of_50ml


def process_amazon_orders(file_path=None):
    """
    This function process all amazon orders generated from seller central orders and turns them into a dictionary.
    it also identifies which orders are outside UK.
    """
    if file_path:
        path = file_path
    else:
        path = 'imports/amazon-orders.csv'
    message = ""
    parcel_force_orders = []
    ups_orders = []
    box_of_500ml = []
    box_of_200ml = []
    order_file = open(path, newline='')
    orders_reader = csv.reader(order_file,  delimiter='\t')
    row_count = 0
    col_count = 0
    for row in orders_reader:
        if row_count < 1:
            for col in row:
                # print(f"col {col_count}: row: {col} \n") #This print is used for debugging and identifying the column names.
                col_count += 1
        elif row_count >= 1:
            # pdb.set_trace()
            orders = {}
            quantity = row[12]
            item_name = row[11]
            order_number = row[0]
            orders['order_number'] = row[0]
            orders['sku'] = row[10]
            orders['item_name'] = row[11]
            orders['quantity'] = row[12]
            orders['email'] = row[7]
            orders['payment_status'] = row[2]
            orders['price'] = row[18]
            orders['customer_name'] = row[16]
            orders['address 1'] = row[17]
            orders['address 2'] = row[18]
            orders['company'] = ''
            orders['city'] = row[20]
            orders['country'] = row[23]
            orders['post_code'] = row[22]
            orders['notes'] = row[21]
            orders['phone'] = row[9]
            orders["status"] = ""

            if quantity:
                try:
                    quantity = int(quantity)
                except:
                    continue
            else:
                quantity = 0

            post_code = orders['post_code'].lower()
            northern_ireland = post_code.startswith('bt')
            restricted_post_codes = True if post_code.startswith(
                'je') else False
            if restricted_post_codes == False:
                if orders['sku'] == "QB-0MQO-FD23" or orders['sku'] == "XC-TWRQ-9ZGO":
                    if quantity >= 2 and quantity <= 8:
                        for i in range(quantity):
                            parcel_force_orders.append(orders)
                    elif quantity == 1:
                        parcel_force_orders.append(orders)
                    else:
                        message += f"order number {orders['order_number']} has {quantity} items and must be sent differently: 5Litre hand sanitiser\n"
                        message += f"Customer name: {orders['customer_name']}\n Phone Number: {orders['phone']}\n"
                        message += f"Address:\n {orders['address 1']}\n {orders['address 2']}\n {orders['city']} \n {orders['post_code']}\n"
                elif orders['sku'] == "CALB11BOX1" or orders['sku'] == "CALB11BOX":
                    if quantity >= 2 and quantity <= 8:
                        for i in range(quantity):
                            box_of_500ml.append(orders)
                    elif quantity == 1:
                        box_of_500ml.append(orders)
                    else:
                        message += f"order number {orders['order_number']} has {quantity} items and must be sent differently:box of 500ml hand sanitiser\n"
                        message += f"Customer name: {orders['customer_name']}\n Phone Number: {orders['phone']}\n"
                        message += f"Address:\n {orders['address 1']}\n {orders['address 2']}\n {orders['city']} \n {orders['post_code']}\n"
                elif orders['sku'] == "CALB08BOX":
                    if quantity >= 2 and quantity <= 8:
                        for i in range(quantity):
                            box_of_200ml.append(orders)
                    elif quantity == 1:
                        box_of_200ml.append(orders)
                    else:
                        message += f"order number {orders['order_number']} has {quantity} items and must be sent differently:box of 200ml hand sanitiser\n"
                        message += f"Customer name: {orders['customer_name']}\n Phone Number: {orders['phone']}\n"
                        message += f"Address:\n {orders['address 1']}\n {orders['address 2']}\n {orders['city']} \n {orders['post_code']}\n"

            elif restricted_post_codes:
                message += f"order number: {order_number} is in the resterticted post code list. Post Code: {post_code}\n"
            else:
                message += f"order number:{order_number} is outside UK. country: {orders['country']} \n"
        row_count += 1

    order_file.close()
    return message, parcel_force_orders, ups_orders, box_of_500ml, box_of_200ml

# def writes_csv()


def create_orders_for_city_sprint(orders):
    today = datetime.datetime.now()  # "13/02/2019"
    max_entries = 240
    file_number = 1
    file_name_date = today.strftime("%Y-%m-%d")
    successful_count = 0
    file_name = "exports/city-sprint-address-labels"
    file = open(
        f'{file_name}-{file_name_date}-{file_number}.csv', 'wb', newline='')
    fieldnames = [
        'Recipient Business Name',
        'Recipient Address Line 1',
        'Recipient Address Line 2',
        'Recipient Address Line 3',
        'Recipient Post Town',
        'Recipient PostCode',
        'Recipient Mobile Number',
        'Recipient Email Address',
        'Special Instructions 1',
        'Special Instructions 2',
        'Reference Number',
    ]
    shippingwriter = csv.DictWriter(
        file, fieldnames=fieldnames)
    shippingwriter.writeheader()

    for order in orders:
        name_and_company = order['customer_name'] + " - " + order['company']
        shippingwriter.writerow({
            'Recipient Business Name': name_and_company,
            'Recipient Address Line 1': order["address 1"],
            'Recipient Address Line 2': order['address 2'],
            'Recipient Address Line 3': "",
            'Recipient Post Town': order["city"],
            'Recipient PostCode': order["post_code"],
            'Recipient Mobile Number': order['phone'],
            'Recipient Email Address': order['email'],
            'Special Instructions 1': order["notes"],
            'Special Instructions 2': "",
            'Reference Number': order["order_number"],
        }
        )
        successful_count += 1
    print(
        f"generated {successful_count} address entries for city-Sprint")
    print(f"{file_name}-{file_name_date}.csv")
    file.close()


def create_ups_file(orders, file_path=None, shop_name=None):
    '''
    Created UPS csv file to be imported
    User this link or more info: https://www.ups.com/gb/en/shipping/create/shipping/create/batch-file.page
    '''
    if file_path:
        return file_path
    else:
        file_path = "exports/"
    today = datetime.datetime.now()  # "13/02/2019"
    max_entries = 200
    # file_number = 1
    message = ""
    file_name_date = today.strftime("%Y-%m-%d")
    successful_count = 0
    dirName = 'exports'
    try:
        os.mkdir(dirName)
        message += f"Directory {dirName} Created \n"
    except:
        pass
    try:
        full_path = f'{file_path}ups-address-labels-{shop_name}-{file_name_date}.csv'
        file = open(
            full_path, 'w', newline='')
        fieldnames = [
            'Contact',
            'Company_or_name',
            'Country',
            'Address_1',
            'Address_2',
            'City',
            'Postal_Code',
            'Telephone',
            'Extension',
            'Email_Address',
            'Weight',
            'Length',
            'Width',
            'Height',
            'Unit_of_Measure',
            'Reference',
            'Packaging_Type',
            'Declared_Value',  # Not required
            'service',
            'Delivery_Confirmation',
            'Email_Notification_1_Address',
            'residential_indicator',
            'bill_transportation_to',
            'number_of_package'

        ]
        shippingwriter = csv.DictWriter(
            file, fieldnames=fieldnames)
        shippingwriter.writeheader()

        for order in orders:
            if order['company']:
                company = order['company'] + " - " + order['customer_name']
            else:
                company = order['customer_name']
            shippingwriter.writerow({
                'Contact': order["customer_name"],
                'Company_or_name': company,
                'Country': "GB",
                'Address_1': order['address 1'],
                'Address_2': order['address 2'],
                'City': order['city'],
                'Postal_Code': order['post_code'],
                'Telephone': order['phone'],
                'Extension': "",
                'Email_Address': order['email'],
                'Weight': 6,
                'Length': 30,
                'Width': 25,
                'Height': 25,
                'Unit_of_Measure': '',
                'Reference': order['order_number'],
                'Packaging_Type': '2',
                'Declared_Value': "48.50",
                'service': "ST",
                'Delivery_Confirmation': 'S',  # meaning signature required
                'Email_Notification_1_Address': order['email'],
                'residential_indicator': 1,
                'bill_transportation_to': 'Shipper',
                'number_of_package': 1
            }
            )
            successful_count += 1

        message += f"{successful_count} orders for {shop_name}"
        file.close()
    except Exception as e:
        message += f"\n{e}\nsomething went wrong creating the UPS file"

    return message


source = input("Please enter S for Shopify and E for Ebay, A for Amazon: \n")
courier = input(
    "please enter the courier: U for UPS and P for Parcel Force (parcel force outside UK Mainland will be exported to UPS): \n")
source = source.upper()
courier = courier.upper()
if source == "S" and courier == "P":
    message, parcel_force_orders, ups_orders = process_shopify_orders()
    print(message)
    create_orders_for_city_sprint(parcel_force_orders)
    create_ups_file(ups_orders, shop_name="Shopify")
elif source == "S" and courier == "U":
    message, parcel_force_orders, ups_orders, box_of_500ml, box_of_200ml, box_of_100ml, box_of_50ml = process_shopify_orders()
    print(message)
    full_list = parcel_force_orders + ups_orders
    full_list = sorted(full_list, key=lambda i: i['order_number'])
    ups = create_ups_file(full_list, shop_name="Shopify - 5litre")
    print(ups)
    ups = create_ups_file(box_of_500ml, shop_name="Shopify - 500ml")
    print(ups)
    ups = create_ups_file(box_of_200ml, shop_name="Shopify - 200ml")
    print(ups)
    ups = create_ups_file(box_of_100ml, shop_name="Shopify - 100ml")
    print(ups)
    ups = create_ups_file(box_of_50ml, shop_name="Shopify - 50ml")
    print(ups)

elif source == "A" and courier == "U":
    message, parcel_force_orders, ups_orders, box_of_500ml, box_of_200ml = process_amazon_orders()
    print(message)
    full_list = parcel_force_orders + ups_orders
    # full_list = full_list, key=lambda i: i['order_number'])
    ups = create_ups_file(full_list, shop_name="Amazon - 5Litre")
    print(ups)
    ups = create_ups_file(box_of_500ml, shop_name="Amazon - 500ml")
    print(ups)
    ups = create_ups_file(box_of_200ml, shop_name="Amazon - 200ml")
    print(ups)
elif source == "E" and courier == "U":
    message, ups_orders, box_of_500ml, box_of_200ml, box_of_100ml = process_ebay_orders()
    print(message)
    # full_list = full_list, key=lambda i: i['order_number'])
    ups = create_ups_file(ups_orders, shop_name="eBay - 5Litre")
    print(ups)
    ups = create_ups_file(box_of_500ml, shop_name="eBay - 500ml")
    print(ups)
    ups = create_ups_file(box_of_200ml, shop_name="eBay - 200ml")
    print(ups)
    ups = create_ups_file(box_of_100ml, shop_name="eBay - 100ml")
    print(ups)
else:
    print(
        f"Wrong Input or the software the entry is not yet supported {source} and {courier} ")
