from flask import Flask, render_template, request, redirect, url_for, session
from flight_processor import process_flight_booking
from __init__ import flightgather, insertOnUserSignUp, checkUsersTable, retrievePassword, storeFlightsInDB, selectUserFlights, updateDelayInfo, deleteRow, recommendDayOfWeek

app = Flask(__name__)
app.secret_key = 'your_secret_key'

users = {}  # Dictionary to store users: {username: password}
flights = []  # Placeholder for storing flights
flight_options = None

globalUser = None

raw_flight_data = None

selected_flights_raw_data = {}

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        #userNotExists = checkUsersTable(username)
        
        #if userNotExists:
        myreturn = insertOnUserSignUp(username, password)
        if myreturn:
            return redirect(url_for('login'))
        else:
            return "Username already exists!"
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global globalUser, flight_options, raw_flight_data
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # if username doesnt exist
        if checkUsersTable(username):
            return "Username doesn't exist! Please sign up!"
        elif retrievePassword(username) == password:
            globalUser = str(username)
            flight_options = [] 
            raw_flight_data = []
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password!"
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    # if 'username' not in session:
    #     return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/choose_recommend', methods=['GET', 'POST'])
def choose_recommended():
    # Here, you can add any logic needed before rendering the recommended page.
    # For example, calculating the recommended days or fetching data.

    global globalUser, flight_options, raw_flight_data
    # if 'username' not in session:
    #     return redirect(url_for('login'))
    if request.method == 'POST' and 'mostcommon' not in request.form:
        initial_airport = request.form.get('initial_airport')
        airline = request.form.get('airline')
        print(initial_airport)
        print(airline)
        recs = recommendDayOfWeek(airline, initial_airport)
    
        print(recs)

        return render_template('mostcommon.html', flights=recs)
    
    return render_template('choose_recommend.html')

@app.route('/book_flight', methods=['GET', 'POST'])
def book_flight():
    global globalUser, flight_options, raw_flight_data
    # if 'username' not in session:
    #     return redirect(url_for('login'))
    if request.method == 'POST' and 'flight_option' not in request.form:
        initial_airport = request.form.get('initial_airport')
        final_airport = request.form.get('final_airport')
        airline = request.form.get('airline')
        month = request.form.get('month')
        day = request.form.get('day')

        flight_options, raw_flight_data = flightgather(initial_airport, final_airport, airline, month, day)
        if flight_options == -1:
            return render_template('invalid.html')

        return render_template('flight_options.html', flight_options=flight_options)

    if 'flight_option' in request.form:
        selected_option = request.form.get('flight_option')
        print("FLIGHT OPTIONS: " + str(flight_options))
        print("SELECTED OPTIONS: " + str(selected_option))
        index = flight_options.index(selected_option)
        if (globalUser not in selected_flights_raw_data):
            selected_flights_raw_data[globalUser] = []
        if raw_flight_data[index] in selected_flights_raw_data[globalUser]:
            pass
        selected_flights_raw_data[globalUser].append(raw_flight_data[index]) 
        print(selected_flights_raw_data)
        # USERNAME, FLIGHT_NUMBER, ORIGIN_AIRPORT, DESTINATION_AIRPORT, DEPARTURE_TIME, AIRLINE, MONTH, DAY
        # USERNAME, FLIGHT_NUMBER, ORIGIN_AIRPORT, DESTINATION_AIRPORT, DEPARTURE_TIME, AIRLINE, MONTH, DAY
        x = raw_flight_data[index]
        storeFlightsInDB(globalUser, x[0], x[1], x[2], x[3], x[4], x[5], x[6])
        #[(436, 'ORD', 'EWR', 'UA', 12, 13, 1557)]
        #storeFlightsInDB()
        flights.append(selected_option)
        return redirect(url_for('my_flights'))

    return render_template('book_flight.html')

@app.route('/my_flights', methods=['GET', 'POST'])
def my_flights():
    # if 'username' not in session:
    #     return redirect(url_for('login'))
    userflight = selectUserFlights(globalUser)  # Retrieve user's flights

    if 'remove_flight' in request.form:
        return redirect(url_for('remove_flight'))  # Redirect to the remove_flight route

    if request.method == 'POST':
        for flight in userflight:
            flight_id = flight[0]  # Assuming flight[0] is the flight ID
            delay_time = request.form.get(f'delay_time_{flight_id}')
            if delay_time:
                # Update the delay time in the selected flights dictionary
                # Add your logic here to update the delay time

                # flight[7] = str((float(delay_time) + float(flight[7])) / 2) 
                #add code for sql
                if(float(delay_time) != float(flight[7])):
                    updateDelayInfo(flight[9], flight[1], delay_time, flight[7]) 
                    userflight = selectUserFlights(globalUser)  
                    return render_template('my_flights.html', flights=userflight)
            
    return render_template('my_flights.html', flights=userflight)

#     return render_template('remove_flight.html')
@app.route('/remove_flight', methods=['GET', 'POST'])
def remove_flight():
    if request.method == 'POST':
        # Retrieve data from the form
        flight_number = request.form.get('flightNumber')
        month = int(request.form.get('month'))
        day = int(request.form.get('day'))

        # Call a function with these values
        #result = your_function_to_handle_removal(flight_number, month, day)
        if deleteRow(globalUser, flight_number, month, day):
            userflight = selectUserFlights(globalUser)
            return render_template('my_flights.html', flights=userflight)
        else:
            return render_template('invalid.html')
        
    # Render the remove flight form if method is GET
    return render_template('remove_flight.html')



# Add other necessary routes and logic

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
