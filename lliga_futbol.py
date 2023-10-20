import requests
import pymongo
import inquirer
import os
import pandas as pd
from pyfiglet import Figlet
from rich.table import Table
from rich.console import Console
from datetime import datetime
from params import atlas_connection_link, api_key, menu_options, menu_options_yes_no
from terminology import in_red, in_yellow, in_blue
#Aquesta vegada utilitzaré "terminology" en comptes de colorama. Docs: https://github.com/juanrgon/terminology

#LA LIGA DE FUTBOL
#Projecte fet TOT en anglès!--------------------------------------------

#The Google Python Style Guide has the following convention:
'''
module_name, package_name, ClassName, method_name, ExceptionName, function_name,
GLOBAL_CONSTANT_NAME, global_var_name, instance_var_name,function_parameter_name,
local_var_name.
'''

# ─────── CONNECT TO MongoDB AND DATABASE ───────
client = pymongo.MongoClient(atlas_connection_link)
db = client["lliga_futbol"]

def create_columns(db):  
    # Create the columns if they dont already exist.
    c_classification = db["classification"]
    c_teams = db["teams"]
    c_matches = db["matches"]
    c_update_times = db["update_times"]
    return c_classification, c_teams, c_matches, c_update_times

#Dictionary of collection names and collection codes.
collection_names = {1:"classification",
                    2:"teams",
                    3:"matches"}

def get_url_base():
    return "http://apiclient.resultados-futbol.com/scripts/api/api.php"

# ─────── API REQUESTS ───────
def send_request_classification(league_id):
    #Asks api for the req "tables" and returns the value api_data["table"]
    URL_BASE = get_url_base()
    
    parameters={"league":league_id,"req":"tables","format":"json","key":api_key}
    r=requests.get(URL_BASE,params=parameters)
    
    if r.status_code == 200:
        api_data = r.json()
        return api_data["table"]
    else:
        print(u"\u26A0 " + (in_red("Query error")))
        
def send_request_teams(league_id):
    #Asks api for the req "teams" and returns the value api_data["team"]
    URL_BASE = get_url_base()
    
    parameters={"league":league_id,"req":"teams","format":"json","key":api_key}
    r=requests.get(URL_BASE,params=parameters)
    
    if r.status_code == 200:
        api_data = r.json()
        return api_data["team"]
    else:
        print(u"\u26A0 " + (in_red("Query error")))

def send_request_matches_date(league_id):
    #Asks api for the req "matchsday" and returns the value api_data["matches"]
    URL_BASE = get_url_base()
    
    v_date = validate_date()
    parameters={"league":league_id,"req":"matchsday", "date":v_date, "format":"json","key":api_key}
    r=requests.get(URL_BASE,params=parameters)
    
    if r.status_code == 200:
        api_data = r.json()
        return api_data["matches"]
    else:
        print(u"\u26A0 " + (in_red("Query error")))

def send_resquest_to_api(collection_code, league_id):
    #Send a different request depending on the league_id given
    match collection_code:
        case 1:
            return send_request_classification(league_id)
        case 2:
            return send_request_teams(league_id)
        case 3:
            return send_request_matches_date(league_id)
        
# ─────── INSERT DATA TO DATABASE ───────
def insert_data_to_database(collection, data, collection_code):

    '''
    #First delete all current content of collection before doing the inserts
    so that updated data is not mixed with outdated data.
    '''  
    
    #Delete current data of the collection sent
    collection.delete_many({}) 
    
    if collection_code == 1: #Collection code for c_classification                            
        insert_collection_1(collection, data)
            
    elif collection_code == 2: #Collection code for c_teams
        insert_collection_2(collection, data)
    
    elif collection_code == 3: #Collection code for c_matches
        insert_collection_3(collection, data)

def insert_update_time(c_update_times, collection_code):
    #Insert the current time and the name of the collection updated.
    data = {
        "collection_name": collection_names[collection_code],
        "date": pd.to_datetime('now'),
    }  

    c_update_times.insert_one(data)

def insert_collection_1(collection, data):
    processed_data = {}
    for team in data:
        processed_data["team_id"] = int(team["id"])
        processed_data["position"] = int(team["pos"])
        processed_data["team_name"] = team["team"]
        processed_data["points"] = int(team["points"])
        collection.insert_one(processed_data)
        del processed_data["_id"]
        
def insert_collection_2(collection, data):
    processed_data = {}
    for team in data:
        processed_data["team_id"] = int(team["id"])
        processed_data["team_name"] = team["nameShow"]
        processed_data["full_team_name"] = team["fullName"]
        processed_data["short_name"] = team["short_name"]
        processed_data["color_code"] = team["color1"]
        collection.insert_one(processed_data)
        del processed_data["_id"]  

def insert_collection_3(collection, data):
    processed_data = {}
    for match in data:
        processed_data["date"] =  match["date"]
        processed_data["time"] =  match["hour"]+":"+match["minute"]
        processed_data["local_team"] =  match["local"]
        processed_data["visitor_team"] =  match["visitor"]
        processed_data["match_result"] =  match["result"]
        collection.insert_one(processed_data)
        del processed_data["_id"]
        
# ─────── HEADER ───────
def print_header(text):
    #Prints the variable "text" as a header with the font selected in Figlet(font=()).
    #Change text variable to change the text printed.
    #Change font value to change the font in which the text is printed.
    f = Figlet(font='slant')
    print(f.renderText(text))

# ─────── PRINT DATA ───────
def print_classification(c_classification, league_id):
    #We use the package "rich.Table" and "rich.Console" to show prettier format of the data.
    console = Console()

    table = Table(
        show_header=True,
        header_style='bold #2070b2',
        title=f'[bold] CLASSIFICATION OF [#2070b2]LEAGUE {str(league_id)}',
    )

    table.add_column('Position', justify='center')
    table.add_column('Team ID', justify='center')
    table.add_column('Team Name', justify='center')
    table.add_column('Points', justify='center')

    for reg in c_classification.find():
        #Special format for the teams in the podium (top 3)
        match (reg["position"]):
            case 1:
                table.add_row('[#FFD700]'+(str(reg["position"])), str(reg["team_id"]), str(reg["team_name"]), str(reg["points"]))
            case 2:
                table.add_row('[#C0C0C0]'+(str(reg["position"])), str(reg["team_id"]), str(reg["team_name"]), str(reg["points"]))
            case 3:
                table.add_row('[#CD7F32]'+ str(reg["position"]), str(reg["team_id"]), str(reg["team_name"]), str(reg["points"])) 

        #Format for teams that are not in the podium (top 3)
        if reg["position"]>3:
            table.add_row(str(reg["position"]), str(reg["team_id"]), str(reg["team_name"]), str(reg["points"]))

    console.print(table)

def print_teams(c_teams, league_id):
    #Package "rich.Table" and "rich.Console" to show prettier format of the data.
    console = Console()

    table = Table(
        show_header=True,
        header_style='bold #2070b2',
        title=f'[bold] TEAMS PARTICIPATING IN [#2070b2]LEAGUE {str(league_id)}',
    )

    table.add_column('Team ID', justify='center')
    table.add_column('Show name', justify='center')
    table.add_column('Full Team Name', justify='center')
    table.add_column('Short Name', justify='center')
    table.add_column('Main Shield Color', justify='center')

    for reg in c_teams.find():
        table.add_row(str(reg["team_id"]), str(reg["team_name"]), str(reg["full_team_name"]), str(reg["short_name"]), '['+str(reg["color_code"])+']'+ str(reg["color_code"]))

    console.print(table)

def print_matches(c_matches, league_id):
    #We use the package "rich.Table" and "rich.Console" to show prettier format of the data.
    console = Console()

    table = Table(
        show_header=True,
        header_style='bold #2070b2',
        title=f'[bold] MATCHES IN [#2070b2]LEAGUE {str(league_id)}',
    )

    table.add_column('Date', justify='center')
    table.add_column('Time', justify='center')
    table.add_column('Local Team', justify='center')
    table.add_column('Visitor Team', justify='center')
    table.add_column('Result', justify='center')

    for reg in c_matches.find():
        table.add_row(str(reg["date"]), str(reg["time"]), str(reg["local_team"]), str(reg["visitor_team"]), str(reg["match_result"]))

    console.print(table)    

def print_last_update(c_update_times, collection_code):
    #Print the date of the last update filtered by the collection name given.
      
    collection_name = collection_names[collection_code]
    print(in_yellow("Last update in collection " + collection_name + ":"))
    print(c_update_times.find_one({"collection_name": collection_name}, sort=[("_id", -1)]).get("date").strftime("%Y-%m-%d %H:%M:%S"))

# ─────── USER INPUT AND INPUT VALIDATION ───────
def validate_date():
#Validate a date and if its valid, return it with format YYYY-MM-DD
    while True:
        try:
            date = input(in_blue("Enter a date in YYYY-MM-DD format: "))
            valid_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print(u"\u26A0 " + in_red("Incorrect format, should be YYYY-MM-DD\n"))
            continue
        return f"{str(valid_date.year)}-{str(valid_date.month)}-{str(valid_date.day)}"

def ask_send_request(collection_code, c_update_times):
    #First we print the date of the last time the collection was updated
    #Then we ask the user if they want to send a request to the api and update the data
    #or work with the data in the database (that might be outdated)
    print_last_update(c_update_times, collection_code)
    while True:
        print(in_yellow("━━━━━━━━━━━━━━━━━━━━━━━"))
        options = [
            inquirer.List('menu_requests',
                        message="Do you want to update the data of collection " + collection_names[collection_code],
                        choices=menu_options_yes_no,
                        ),
        ]
        answers = inquirer.prompt(options)


        os.system('cls' if os.name == 'nt' else 'clear') #Clear console content

                #Options of the menu_requests (function "ask_send_request")
        return answers['menu_requests'] == 'Yes'                

# ─────── MENUS ───────
def main_menu(c_classification, c_teams, c_matches, c_update_times):
    while True:
            print(in_yellow("━━━━━━━━━━━━━━━━━━━━━━━"))
            options = [
                inquirer.List('main_menu',
                            message="Choose an option from the menu",
                            choices=menu_options,
                            ),
            ]
            answers = inquirer.prompt(options)
            
            os.system('cls' if os.name == 'nt' else 'clear') #Clear console content
            main_menu_options(c_classification, c_teams, c_matches, answers, c_update_times)
            
            if answers['main_menu'] == 'Quit application':
                    break 

def main_menu_options(c_classification, c_teams, c_matches, answers, c_update_times):
    #Options of the main menu (not counting the quit application option)
    if answers['main_menu'] == 'Consult the classification':
        collection_code = 1
        if ask_send_request(collection_code, c_update_times):
            extracted_main_menu_options(
                collection_code, c_classification, c_update_times
            )
        print_classification(c_classification, 1)

    if answers['main_menu'] == 'List the results of matches on a date':
        collection_code = 3
        if status_true_false := ask_send_request(
            collection_code, c_update_times
        ):
            api_data = send_resquest_to_api(collection_code, 1)
            if api_data == False:
                print(u"\u26A0 " + (in_red("There's no matches for this date")))
            else:
                insert_data_to_database(c_matches, api_data, collection_code)
                insert_update_time(c_update_times, collection_code)
                print_matches(c_matches, 1)
        elif status_true_false == False:
            print_matches(c_matches, 1)

    if answers['main_menu'] == 'List all teams in the League':
        collection_code = 2
        if ask_send_request(collection_code, c_update_times):
            extracted_main_menu_options(collection_code, c_teams, c_update_times)
        print_teams(c_teams, 1)       

# ─────── EXTRACTED FUNCTIONS  ───────
def extracted_main_menu_options(collection_code, arg1, c_update_times):
    api_data = send_resquest_to_api(collection_code, 1)
    insert_data_to_database(arg1, api_data, collection_code)
    insert_update_time(c_update_times, collection_code)       

# ─────── MAIN  ───────
def main(db):
    os.system('cls' if os.name == 'nt' else 'clear') #Clear console content
    c_classification, c_teams, c_matches, c_update_times = create_columns(db)
    print_header("Football League")
    main_menu(c_classification, c_teams, c_matches, c_update_times)

main(db)

#Close connection to the Database
client.close()