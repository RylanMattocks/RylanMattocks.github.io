import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import sqlite3
import hashlib
import math
import logging

############# Loading data into dataframe
DATA_URL = ('indianapolis_temp.csv')

def load_data(nrows):
    data = pd.read_csv(DATA_URL, parse_dates = 
        {'Date' : ['Year','Month','Day']}, keep_date_col=True, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    return data

# Load all rows of data into the dataframe.
data = load_data(9266)

# Create new column for Seasons
conditions = [
    (pd.to_numeric(data['month']) >= 6) & (pd.to_numeric(data['month']) <= 8),
    (pd.to_numeric(data['month']) >= 9) & (pd.to_numeric(data['month']) <= 11),
    (pd.to_numeric(data['month']) >= 3) & (pd.to_numeric(data['month']) <= 5),
    (pd.to_numeric(data['month']) >= 12) | (pd.to_numeric(data['month']) <= 2)
]
values = ['summer', 'fall', 'spring', 'winter']
data['season'] = np.select(conditions, values)

############# Creating Database connection
conn = sqlite3.connect('dbdata.db')
c = conn.cursor()

############# Creating functions to query database

# Create table in database if one doesn't exist
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')

# Add hashed username and password combo into database
def add_userdata(username,password):
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (hashlib.md5(str.encode(username)).hexdigest(),hashlib.md5(str.encode(password)).hexdigest()))
    conn.commit()

# Select hashed username and password from database and return if exists
def login_user(username,password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (hashlib.md5(str.encode(username)).hexdigest(),hashlib.md5(str.encode(password)).hexdigest()))
    dbdata = c.fetchall()
    return dbdata

# View all users in the database
def view_all_users():
    c.execute('SELECT * FROM userstable')
    dbdata = c.fetchall()
    return dbdata

############# Creating log files
# Setup function to create log file
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
def setup_logger(name, log_file, level = logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        logger.handlers=[]

    logger.addHandler(handler)

    return logger
    
# Create log file
file_logger = setup_logger('first_logger', 'invalidentries.log')

############# Start of Application

# Create variables for use in data
GET_SEASONS = ['winter', 'spring', 'summer', 'fall']
COLOR = ['#fa4115','#bb2852','#1aa6c2','#49eb6e','#0a4dca','#fbb6c0','#3ca900','#b7a1f4','#3fcdf9','#c59121','#171ba2', '#870a11']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
YEARS = []
for x in range(1995,2020):
    YEARS.append(int(x))
YEARS_STRING = []
for x in range(1995,2020):
    YEARS_STRING.append(str(x))
DAYS = []
for x in range(0,31):
    DAYS.append(str(x + 1))
LEAP_YEARS = []
for x in range(0,276):
    LEAP_YEARS.append(1900 + (4*x))
NON_LEAP_YEARS = [1900, 2100, 2200, 2300, 2500, 2600, 2700, 2900, 3000]
for x in range(len(NON_LEAP_YEARS)):
    LEAP_YEARS.remove(NON_LEAP_YEARS[x])

# Application Title
st.title('Indianapolis Weather Data')

# Application Sidebar Selections
menu = ['Login', 'Sign Up']
choice = st.sidebar.selectbox("Menu", menu)

# If the user chooses the Login menu in sidebar
if choice == 'Login':
    # Tell user to login or sign up
    # Retrieve user input from login fields
    st.subheader('Please Login or Sign Up')
    username = st.sidebar.text_input('User Name')
    password = st.sidebar.text_input('Password', type='password')

    # If user selects login checkbox
    if st.sidebar.checkbox('Login'):
        # Create database table if non-existent
        # Query database to check if username and password combo exists and save as boolean
        create_usertable()
        result = login_user(username,password)

        # If username and password combo exists give access to view data
        if result:
            # Notify user of successful login
            st.success('Logged in as {}'.format(username))

            # Create menus to display data
            task = st.selectbox('Weather Data', ['Seasonal', 'Monthly', 'Yearly', 'Prediction'])
            
            ############# Show data based on selected tab
            if task == 'Seasonal':
                # USING METEOROLOGICAL SEASONS
                    # December 1 to February 28 (WINTER)
                    # March 1 to May 31 (SPRING)
                    # June 1 to August 31 (SUMMER)
                    # September 1 to November 30 (FALL)
                # Create Bar Chart for seasonal temperatures
                st.subheader('Temperatures by Season')

                # Create slider to display data by year
                SLIDER = alt.binding_range(min=1995, max=2019, step=1, name = 'Year')
                SELECT_YEAR = alt.selection_single(name='Year', fields=['Year'],
                                                bind=SLIDER, init={'Year': 2019})

                # Create matrix to store temperatures by year
                SEASONAL_DATA = []
                for x in range(1995,2020):
                    a=[]
                    for y in range(0,4):
                        a.append(0)
                    SEASONAL_DATA.append(a)

                # Populate matrix with temperature data
                for i in range(len(SEASONAL_DATA)):
                    for j in range(len(SEASONAL_DATA[0])):
                        SEASONAL_DATA[i][j]=(data.loc[(data['season'] == GET_SEASONS[j]) & (data['year'] == str(i+1995)), 'avgtemperature'].sum() / data.loc[(data['season'] == GET_SEASONS[j]) & (data['year'] == str(i+1995)), 'avgtemperature'].count())

                # Create dataframe
                # Label columns by Season
                # Create column for years
                SEASONAL_DF = pd.DataFrame(SEASONAL_DATA)
                SEASONAL_DF.columns = ['Winter', 'Spring', 'Summer', 'Fall']
                SEASONAL_DF['Year'] = YEARS

                # Change dataframe to long form data
                # Add column for date range of each season
                SEASONAL_CLEAN_DF = SEASONAL_DF.melt('Year', value_name= 'Temperature (°F)', var_name= 'Seasons')
                SEASONAL_CLEAN_DF['Range'] = [0] * 100
                SEASONAL_CLEAN_DF['Temperature (°F)'] = SEASONAL_CLEAN_DF['Temperature (°F)'].astype(float)
                SEASONAL_CLEAN_DF['Temperature (°F)'] = SEASONAL_CLEAN_DF['Temperature (°F)'].round(decimals = 2)
                SEASONAL_CLEAN_DF.loc[SEASONAL_CLEAN_DF['Seasons'] == 'Winter', 'Range'] = 'December 1 - February 28/29'
                SEASONAL_CLEAN_DF.loc[SEASONAL_CLEAN_DF['Seasons'] == 'Spring', 'Range'] = 'March 1 - May 31'
                SEASONAL_CLEAN_DF.loc[SEASONAL_CLEAN_DF['Seasons'] == 'Summer', 'Range'] = 'June 1 - August 31'
                SEASONAL_CLEAN_DF.loc[SEASONAL_CLEAN_DF['Seasons'] == 'Fall', 'Range'] = 'September 1 - November 30'

                # Create altair chart to display dataframe as bar graph
                SEASON_CHART = alt.Chart(SEASONAL_CLEAN_DF).mark_bar().encode(x=alt.X('Seasons', sort = None), y = alt.Y('Temperature (°F)', scale = alt.Scale(domain = (0, 80))), color = 'Seasons', 
                    tooltip = [alt.Tooltip('Temperature (°F)', title = 'Farenheit'), alt.Tooltip('Range', title = 'Date Range')]).add_selection(SELECT_YEAR).transform_filter(SELECT_YEAR).interactive()
                st.altair_chart(SEASON_CHART, use_container_width=True)

            elif task == 'Monthly':
                # Create Two Line Charts for monthly temperatures and monthly averages
                # Create line chart for monthly
                st.subheader('Monthly Temperatures by Day')

                # Create dataframe from original data dropping not needed columns
                # Change year to integer
                MONTH_DATA = data.drop(columns = ['date', 'region', 'country', 'state', 'city', 'season'])
                MONTH_DATA = MONTH_DATA.astype({'year' : 'int'})

                # Create slider to display data by year
                SLIDER2 = alt.binding_range(min=1995, max=2019, step=1, name = 'Year')
                SELECT_YEAR2 = alt.selection_single(name='year', fields=['year'],
                                                bind=SLIDER2, init={'year': 2019})

                # Create and populate column to hold name of month i.e "January"
                MONTH_DATA['name'] = ['a'] * 9265
                for x in range(13):
                    MONTH_DATA.loc[MONTH_DATA['month'] == str(x), 'name'] = MONTHS[x - 1]

                # Create selection for tooltip hover
                selection = alt.selection_single(fields=['day'], nearest=True, on='mouseover', empty='none', clear='mouseout')

                # Create chart for month line
                # Create chart for temperature data points
                # Create chart to display tooltip on vertical line
                MONTH_CHART = alt.Chart(MONTH_DATA).mark_line().encode(x = alt.X('day', sort = None, title = 'Day'), y = alt.Y('avgtemperature', title = 'Temperature (°F)'), color = alt.Color('name', scale = alt.Scale(domain = MONTHS, range = COLOR), title = 'Month'))
                MONTH_POINT = alt.Chart(MONTH_DATA).mark_circle().encode(x = alt.X('day', sort = None, title = 'Day'), y = alt.Y('avgtemperature', title = 'Temperature (°F)'), color = alt.Color('name', scale = alt.Scale(domain = MONTHS, range = COLOR), title = 'Month'), tooltip = [alt.Tooltip('avgtemperature', title = 'Farenheit')])
                MONTH_TOOLTIP = alt.Chart(MONTH_DATA).transform_pivot('name', value='avgtemperature', groupby = ['day']).mark_rule(color = 'steelblue').encode(x = alt.X('day', sort = None, title = 'Day'), opacity = alt.condition(selection, alt.value(1), alt.value(0)), tooltip = [alt.Tooltip(c, type = 'quantitative') for c in MONTHS]).add_selection(selection)

                # Dislpay Charts as line graph
                st.altair_chart((MONTH_CHART + MONTH_POINT + MONTH_TOOLTIP).add_selection(SELECT_YEAR2).transform_filter(SELECT_YEAR2).interactive(), use_container_width=True)
            
                # Create line chart for monthly averages
                st.subheader('Average Monthly Temperatures Since 1995')

                # Create matrix to hold monthly data
                MONTH_DATA_AVG = []
                for x in range(1,32):
                    a=[]
                    for y in range(1,13):
                        a.append(0)
                    MONTH_DATA_AVG.append(a)
                
                # Populate matrix with monthly temperatures
                for i in range(len(MONTH_DATA_AVG)):
                    for j in range(len(MONTH_DATA_AVG[0])):
                        if (data.loc[(data['month'] == str(j+1)) & (data['day'] == str(i+1)), 'avgtemperature'].sum()) != 0 or (data.loc[(data['month'] == str(j+1)) & (data['day'] == str(i+1)), 'avgtemperature'].count()) != 0:
                            MONTH_DATA_AVG[i][j]=(data.loc[(data['month'] == str(j+1)) & (data['day'] == str(i+1)), 'avgtemperature'].sum() / data.loc[(data['month'] == str(j+1)) & (data['day'] == str(i+1)), 'avgtemperature'].count())
                        else:
                            file_logger.info('The month does not have any more days')
                            MONTH_DATA_AVG[i][j]=np.nan
                
                # Create dataframe
                # Label columns by month
                # Create column to hold day values
                MONTH_DF_AVG = pd.DataFrame(MONTH_DATA_AVG)
                MONTH_DF_AVG.columns = MONTHS
                MONTH_DF_AVG['Days'] = DAYS

                # Change dataframe to long form data
                MONTH_DATA_AVG_CLEAN = MONTH_DF_AVG.melt('Days', value_name= 'Temperature (°F)', var_name= 'Months')
                MONTH_DATA_AVG_CLEAN['Temperature (°F)'] = MONTH_DATA_AVG_CLEAN['Temperature (°F)'].round(decimals = 1)

                # Create selection for tooltip hover
                selection2 = alt.selection_single(fields=['Days'], nearest=True, on='mouseover', empty='none', clear='mouseout')

                # Create chart for month line
                # Create chart to display tooltip on vertical line
                MONTH_AVG_CHART = alt.Chart(MONTH_DATA_AVG_CLEAN).mark_line().encode(x = alt.X('Days', sort = None), y = alt.Y('Temperature (°F)', scale = alt.Scale(domain = (20,80))), color = alt.Color('Months', scale = alt.Scale(domain = MONTHS, range = COLOR)))
                MONTH_AVG_RULE = alt.Chart(MONTH_DATA_AVG_CLEAN).transform_pivot('Months', value='Temperature (°F)', groupby = ['Days']).mark_rule(color = 'steelblue').encode(x = alt.X('Days', sort = None, title = 'Days'), opacity = alt.condition(selection2, alt.value(1), alt.value(0)), tooltip = [alt.Tooltip(c, type = 'quantitative') for c in MONTHS]).add_selection(selection2)

                # Display charts as line graph
                st.altair_chart((MONTH_AVG_CHART + MONTH_AVG_RULE).interactive(), use_container_width=True)

            elif task == 'Yearly':
                # Create bubble chart with trend line for yearly average temperature
                st.subheader('Yearly Temperatures')

                # Create and populate array to hold average temperature for each year
                YEARLY_DATA = []
                for x in range(1995,2020):
                    YEARLY_DATA.append(data.loc[data['year'] == str(x), 'avgtemperature'].sum() / data.loc[data['year'] == str(x), 'avgtemperature'].count())

                # Create dataframe for temperature data
                YEARLY_DF = pd.DataFrame({'Years' : YEARS_STRING, 'Temperature (°F)' : YEARLY_DATA})

                # Create bubble chart for yearly average temperature
                # Create trend line to show temperature change per year
                YEARLY_CHART_BUBBLE = alt.Chart(YEARLY_DF).mark_point(color = 'red').encode(x = alt.X('Years', sort = None), y = alt.Y('Temperature (°F)', scale = alt.Scale(domain = (49,58))))
                YEARLY_CHART_TREND = YEARLY_CHART_BUBBLE.transform_regression('Years', 'Temperature (°F)').mark_line(color = 'orange').encode()
                
                # Display Charts as bubble graph with trend line
                st.altair_chart((YEARLY_CHART_BUBBLE + YEARLY_CHART_TREND).interactive(), use_container_width=True)

            elif task == 'Prediction':
                # Create temperature prediction based on date input < 12/31/3000
                st.subheader('Temperature Prediction')

                # User input fields
                day_prediction = st.number_input('Day', min_value = 1, max_value = 31, step = 1)
                month_prediction = st.selectbox('Month', MONTHS)
                year_prediction = st.number_input('Year', min_value = 2021, max_value = 3000, step = 1)

                # Verify user has input a correct date
                correct_format = True
                leap_year = False
                short_months = {'april', 'june', 'september', 'november'}
                month_index = -1

                # When user presses enter check if date is entered correctly
                if st.button('Enter'):
                    # Check if year entered is a leap year
                    for x in range(len(LEAP_YEARS)):
                        if year_prediction == LEAP_YEARS[x]:
                            leap_year = True
                            break;

                    # Check if month input has less than 31 days
                    # Check if day input is greater that 30
                    # Give warning message if True
                    if month_prediction.lower() in short_months:
                        if day_prediction == 31:
                            file_logger.info('The month you have entered does not have 31 Days')
                            st.warning('The month you have entered does not have 31 Days')
                            correct_format = False

                    # Check if month entered is February
                    # Check if day selected is under 30
                    # Check if day selected is 29 and is not a leap year
                    # Give warning message if True
                    if month_prediction.lower() == 'february':
                        if day_prediction == 30 or day_prediction == 31:
                            st.warning('The month you have enetered does not have more than 30 days')
                            file_logger.info('The month you have enetered does not have more than 30 days')
                            correct_format = False
                        if day_prediction == 29 and leap_year == False:
                            file_logger.info('This is not a leap year')
                            st.warning('This is not a leap year')
                            correct_format = False

                    # Set month index to months #
                    for x in range(len(MONTHS)):
                        if MONTHS[x] == month_prediction:
                            month_index = x + 1
                            break;

                    # If data entered is in correct format predict temperature data
                    if correct_format:
                        # Create list of what years have temperature data of given date
                        temperature_years = []
                        for x in range(1995, 2021):
                            if data.loc[(data['month'] == str(month_index)) & (data['day'] == str(day_prediction)) & (data['year'] == str(x)), 'avgtemperature'].any():
                                temperature_years.append(str(x))
                        
                        # Get temperature data for all previous years of given date
                        temperature_data = []
                        if data.loc[(data['month'] == str(month_index)) & (data['day'] == str(day_prediction)), 'avgtemperature'].any():
                                temperature_data.append(data.loc[(data['month'] == str(month_index)) & (data['day'] == str(day_prediction)), 'avgtemperature'])
                        
                        # Create dataframe and transform rows and columns
                        # Add year column
                        temperature_df = pd.DataFrame(temperature_data)
                        temperature_df.columns = temperature_years
                        temperature_clean_df = temperature_df.T
                        temperature_clean_df['Year'] = temperature_years
                        
                        # Create X variables for regression equation
                        temperature_clean_df.Year = temperature_clean_df.Year.astype(int)
                        total_year = (temperature_clean_df['Year']).sum()
                        mean_year = (int(total_year) / len(temperature_clean_df['Year']))

                        year_difference = []
                        for x in range(len(temperature_years)):
                            year_difference.append(int(temperature_years[x]) - mean_year)

                        sum_of_squares = 0
                        for x in range(len(year_difference)):
                            sum_of_squares = (sum_of_squares + (year_difference[x] * year_difference[x]))

                        # Create Y variables for regression equation
                        total_temp = temperature_clean_df['avgtemperature'].sum()
                        mean_temp = (total_temp / len(temperature_clean_df['avgtemperature']))

                        temp_difference = []
                        for x in range(len(temperature_clean_df['avgtemperature'])):
                            temp_difference.append(((temperature_clean_df['avgtemperature']).iloc[x]) - mean_temp)

                        sum_of_products = 0
                        for x in range(len(temp_difference)):
                            sum_of_products = (sum_of_products + (temp_difference[x] * year_difference[x]))
                        
                        # Create regression equation
                        b = (sum_of_products / sum_of_squares)
                        a = (mean_temp - (b * mean_year))
                        regression_equation = ((b * year_prediction) + a)

                        # Get standard deviation of temperatures
                        # Create array to hold predicted and actual data
                        y_actual = []
                        y_predicted = []

                        # Populate arrays with predicted and actual data
                        for x in range(len(temperature_clean_df['avgtemperature'])):
                            y_actual.append(((temperature_clean_df['avgtemperature']).iloc[x]))
                        for x in range(len(temperature_years)):
                            y_predicted.append((b * 1995) + a)
                        
                        # Find means square error and root mean square error
                        MSE = np.square(np.subtract(y_actual,y_predicted)).mean() 
                        RMSE = math.sqrt(MSE)

                        # Create variables to use for regression line
                        x_variables = [1995, 2020]
                        y_variables = [((b * 1995) + a), ((b * 2020) + a)]

                        # Create selection for tooltip hover
                        selection3 = alt.selection_single(fields=['Year'], nearest=True, on='mouseover', empty='none', clear='mouseout')

                        # Create dataframe for regression line
                        regression_line_df = pd.DataFrame({'Years' : x_variables, 'Temperature' : y_variables})

                        # Create charts to display bubble chart and regression line
                        # Create chart for regression line
                        # Create chart for data points
                        # Create chart for vertical tooltip
                        regression_line = alt.Chart(regression_line_df).mark_line(color = 'red').encode(x = alt.X('Years', sort = None, scale = alt.Scale(domain = (1995, 2020))), y = alt.Y('Temperature'))
                        data_points = alt.Chart(temperature_clean_df).mark_point().encode(x = alt.X('Year', sort = None, scale = alt.Scale(domain = (1995, 2020))), y = alt.Y('avgtemperature', title = 'Temperature'))
                        regression_rule = alt.Chart(temperature_clean_df).mark_rule(color = 'steelblue').encode(x = alt.X('Year', sort = None, scale = alt.Scale(domain = (1995, 2020))), opacity = alt.condition(selection3, alt.value(1), alt.value(0)),tooltip = alt.Tooltip('avgtemperature')).add_selection(selection3)

                        # Display bubble chart and regression line
                        st.altair_chart((data_points + regression_line + regression_rule).properties(width = 600).interactive())

                        # Create variables for regression line prediction
                        y_variables2 = [((b * 1995) + a), regression_equation]
                        x_variables2 = [1995, year_prediction]

                        # Create dataframe and chart for regression line prediction
                        regression_line_df2 = pd.DataFrame({'Years' : x_variables2, 'Temperature' : y_variables2})
                        regression_line2 = alt.Chart(regression_line_df2).mark_line(color = 'red').encode(x = alt.X('Years', sort = None, scale = alt.Scale(domain = (1995, year_prediction))), y = alt.Y('Temperature')).properties(width = (1250))
                        
                        # Display predicted temperature for given date
                        st.write('The predicted temperature for ', month_prediction, ' ', str(day_prediction), ', ', str(year_prediction), ' is: ', str(regression_equation.round(decimals = 2)), '+/-', str(round(RMSE, 2)), '°F')

                        # Display regression line prediction
                        st.altair_chart(regression_line2)
                
        # If username and password combo does not exist give error message
        else:
            st.warning('Incorrect Username/Password')
            file_logger.info('Incorrect Username/Password')

# If the user chooses the Sign Up menu in sidebar
elif choice == 'Sign Up':
    # Tell user to sign up
    # Retrieve user input from signup fields
    st.subheader('Sign Up')
    new_user = st.text_input('Username')
    new_password = st.text_input('Password', type = 'password')

    # When user presses sign up button
    if st.button('Sign Up'):
        # Create user table in database if non-existent
        # Add user data to table
        # Display success to user
        create_usertable()
        add_userdata(new_user, new_password)
        st.success('Account Successfully Created')
        st.info('Navigate to login menu to proceed')

