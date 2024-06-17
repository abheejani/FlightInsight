import os 
import sqlalchemy
from yaml import load, Loader
from flask import Flask
import sys

import pymysql 
from sqlalchemy import text 
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc

def init_connection_engine():
    # detect env local or gcp
    if os.environ.get('GAE_ENV') != 'standard':
        try:
            variables = load(open("app.yaml"), Loader=Loader)
        except OSError as e:
            print("Make sure you have the app.yaml file setup")
            #os.exit()
            sys.exit()

        env_variables = variables['env_variables']
        for var in env_variables:
            os.environ[var] = env_variables[var]

    # make sure to add a network 
    connect_string = f'mysql+pymysql://root:cs411@35.225.178.245/proj'
    pool = sqlalchemy.create_engine(connect_string)
    return pool

def flightgather(initial_airport, final_airport, airline, month, day):
    callStoredProcedure(airline, initial_airport)
    db = init_connection_engine()
    with db.connect() as conn:
        query = f"Select FLIGHT_NUMBER, ORIGIN_AIRPORT, DESTINATION_AIRPORT, AIRLINE, MONTH, DAY, DEPARTURE_TIME from flights WHERE ORIGIN_AIRPORT = '{initial_airport}' AND DESTINATION_AIRPORT = '{final_airport}' AND MONTH = '{month}' AND DAY = '{day}' AND AIRLINE = '{airline}'"
        results = conn.execute(text(query))
        flight_infos = []
        raw_flight_data = []
        if results is None:
            return -1, -1
        for x in results:
            flight_info = str(x[3]) + str(x[0]) + " FROM " + str(x[1]) + " TO " + str(x[2])
            flight_infos.append(flight_info)
            raw_flight_data.append(x)
        if not flight_infos:
            return -1, -1
        
        return flight_infos, raw_flight_data

def checkUsersTable(username):
    db = init_connection_engine()
    with db.connect() as conn: 
        query = f"SELECT USER_NAME FROM users where USER_NAME = '{username}'"
        results = conn.execute(text(query)).fetchone()

    return results is None

def insertOnUserSignUp(username, password):
    db = init_connection_engine()
    with db.connect() as conn: 
        # query = f"INSERT INTO users (USER_NAME, PASSWORD) VALUES ('{username}', '{password}')"
        # conn.execute(text(query))
        # conn.commit()
        query = f"INSERT INTO users (USER_NAME, PASSWORD) VALUES ('{username}', '{password}')"

        try:
            conn.execute(text(query))
            conn.commit()
        except exc.SQLAlchemyError as e:
            print("An error occurred:", e)
            # Handle the specific error caused by the trigger
            if "Duplicate username" in str(e):
                print("Username already exists!")
                return 0 
    return 1

def retrievePassword(username):
    db = init_connection_engine()
    with db.connect() as conn: 
        query = f"SELECT PASSWORD FROM users WHERE USER_NAME = '{username}'"
        results = conn.execute(text(query)) 
        myPass = []
        for x in results:
            myPass.append(x[0])
    return myPass[0]

def storeFlightsInDB(username, flight_num, initial_airport, final_airport, airline, month, day, departure_time):
    db = init_connection_engine()
    with db.connect() as conn:
        query = f"INSERT INTO itinerary (USERNAME, FLIGHT_NUMBER, ORIGIN_AIRPORT, DESTINATION_AIRPORT, DEPARTURE_TIME, AIRLINE, MONTH, DAY) VALUES ('{username}', '{flight_num}', '{initial_airport}', '{final_airport}', '{departure_time}', '{airline}', '{month}', '{day}')"
        conn.execute(text(query))
        conn.commit()

def selectUserFlights(username):
    db = init_connection_engine()
    with db.connect() as conn:
        query = f"""
            SELECT i.FLIGHT_NUMBER, i.ORIGIN_AIRPORT, i.DESTINATION_AIRPORT, i.DEPARTURE_TIME, 
            a.AIRLINE, i.MONTH, i.DAY, fd.total_delay, fd.delay_category, i.airline
            FROM itinerary i 
            JOIN airlines a ON i.AIRLINE = a.IATA_CODE 
            JOIN flight_delays fd ON i.AIRLINE = fd.airline AND i.ORIGIN_AIRPORT = fd.origin_airport
            WHERE i.USERNAME = '{username}'
        """
        results = conn.execute(text(query))
        userInfo = []
        for booking in results:
            temp = []
            for i in booking:
                temp.append(i)
            userInfo.append(temp)
        #print(userInfo)
    return userInfo

def check_existence(airline_code, orig_airport_code):
    db = init_connection_engine()
    with db.connect() as conn:
        query = f"SELECT COUNT(*) FROM flight_delays WHERE airline = '{airline_code}' AND origin_airport = '{orig_airport_code}'"
        result = conn.execute(text(query)).fetchone()
        count = result[0] if result else 0
        return count > 0
        
def callStoredProcedure(airlineCode, origAirportCode):
    if not check_existence(airlineCode, origAirportCode):
        db2 = init_connection_engine()
        with db2.connect() as conn2:
            query2 = f"call SP10('{airlineCode}', '{origAirportCode}')"
            # flight_delaysairline, origin_airport
            conn2.execute(text(query2))
            conn2.commit()

def updateDelayInfo(airlineCode, origAirportCode, delay_time, curr_delay): 
    newdelay = (float(delay_time) + float(curr_delay)) / 2
    print("newdelay" + str(newdelay))
    db = init_connection_engine()
    with db.connect() as conn: 
        query = f"""
        UPDATE flight_delays
        SET total_delay = '{newdelay}',
            delay_category = CASE
                WHEN {newdelay} < 0 THEN 'Early'
                WHEN {newdelay} < 10 THEN 'Small Delay'
                WHEN {newdelay} < 30 THEN 'Medium Delay'
                ELSE 'Large Delay'
            END
        WHERE airline = '{airlineCode}' AND origin_airport = '{origAirportCode}'
        """

        conn.execute(text(query))
        conn.commit()

def checkUserFlightExists(username, flightNumber, month, day):
    db = init_connection_engine()
    with db.connect() as conn: 
    # check if flightNum, username, month, day are in a row
        query = f"""
            SELECT COUNT(*) 
            FROM itinerary 
            WHERE USERNAME = '{username}' AND FLIGHT_NUMBER = '{flightNumber}' AND MONTH = '{month}' AND DAY = '{day}'
            """
        result = conn.execute(text(query)).fetchone()
    return result[0] > 0


def deleteRow(username, flightNumber, month, day):
    if checkUserFlightExists(username, flightNumber, month, day):
        db = init_connection_engine()
        with db.connect() as conn:
            delete_query = f"""
                DELETE FROM itinerary 
                WHERE USERNAME = '{username}' AND FLIGHT_NUMBER = '{flightNumber}' AND MONTH = '{month}' AND DAY = '{day}'
                """
            conn.execute(text(delete_query))
            conn.commit()
            return True
    else:
        return False
    
def recommendDayOfWeek(airline, airport):
    db = init_connection_engine()
    with db.connect() as conn:
        query = f"""
    SELECT 
        F.ORIGIN_AIRPORT,
        CASE 
            WHEN F.DAY_OF_WEEK = 1 THEN 'Sunday'
            WHEN F.DAY_OF_WEEK = 2 THEN 'Monday'
            WHEN F.DAY_OF_WEEK = 3 THEN 'Tuesday'
            WHEN F.DAY_OF_WEEK = 4 THEN 'Wednesday'
            WHEN F.DAY_OF_WEEK = 5 THEN 'Thursday'
            WHEN F.DAY_OF_WEEK = 6 THEN 'Friday'
            WHEN F.DAY_OF_WEEK = 7 THEN 'Saturday'
        END as DayOfWeek,
        F.AIRLINE,
        A.AIRLINE as AirlineName,
        ROUND(AVG(F.DEPARTURE_DELAY), 2) as AvgDelay
    FROM 
        flights F 
    JOIN 
        airlines A 
    ON 
        F.AIRLINE = A.IATA_CODE 
    WHERE 
        F.AIRLINE = '{airline}' 
        AND F.ORIGIN_AIRPORT = '{airport}' 
    GROUP BY 
        F.DAY_OF_WEEK, F.AIRLINE, A.AIRLINE, F.ORIGIN_AIRPORT 
    ORDER BY 
        AvgDelay
"""
        results = conn.execute(text(query))
        print(results)
        
        flightInfo = []
        for row in results:
            temp = []
            for i in row:
                temp.append(i)
            flightInfo.append(temp)
    return flightInfo
        



