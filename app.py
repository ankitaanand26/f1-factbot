from dotenv import load_dotenv
import streamlit as st
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.messages import AIMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
import concurrent.futures

def get_sql_chain():
    template = """
        Your are an SQLite expert.
        Given a question from the user, you need to create syntactically correct queries.
        The database contains tables with interconnected information and statistics about Formula 1 races, teams, and drivers. 
        Below, each table is described briefly with the columns and a short description of each column.

        Table Descriptions:
        - circuits - Circuits are tracks on which Formula 1 races take place. Columns: circuitID, circuitRef(reference name for the circuit), name, location (city in which the circuit is located), country, lat (latitude), long (longitude), alt (altitude) and url (Wikipedia link for the circuit).
        - constructor_results - Constructor is another name to refer to teams competing in Formula 1. Columns: constructorResultsID, raceID, constructorID, points and status.
        - constructor_standings - This table gives information about where in the points table each constructor was placed after every race. Columns: constructorStandingsID, raceID, constructorID, points, position (position of the constructor after that particular race in the standings), positionText, wins.
        - constructors - Columns: constructorID, constructorRef (reference name for each constructor), name, nationality and url (Wikipedia link for the constructor) 
        - driver_standings - This table gives information about where in the points table each driver was placed after every race. Columns: driverStandingsID, raceID, driverID, points, position, positionText and wins. 
        - drivers - This table gives details of every driver who has raced in Formula 1. Columns: driverID, driverRef(reference name for a driver), number (car number), code (3 letter code for each driver), forename, surname, dob (date of birth), nationality, url (Wikipedia page of the driver for more information).
        - lap_times - This table gives information about the time taken to complete a particular lap in a particular race by a particular driver. Columns: raceID, driverID, lap (lap number in the race), position (position of the driver in the race), time (time taken for the lap), milliseconds (time in milliseconds)
        - pit_stops - A driver stops during the race in the pitlane to make minor changes to the car. This table gives information about pitstops made during a particular race. Columns: raceID, driverID, stop (pit stop number in the race by that driver), lap (lap in which stop was made), time (time of the day at which stop was made), duration (time taken during the stop), milliseconds (duration in milliseconds)
        - qualifying - This table contains information about qualification that happens before a race. Columns: qualifyID, raceID, driverID, constructorID, number (car number), q1 (lap time in qualification round 1 also referred to as Q1), q2 (lap time in q2), q3 (lap time in q3)
        - races - This table contains information about each race held each season. Columns: raceID, year (year in which the race took place), round (nth race of the year, n being a number), circuitID, name, date, time (time of race start), fp1_date (fp stands for free practice), fp1_time, fp2_date, fp2_time, quali_date, quali_time, sprint_date (date of sprint race), sprint_time
        - results - This table contains results of each race for each driver. Columns: resultID, raceID, driverID, constructorID, number (car number), grid (position at the start of the race), position (at the end of the race), points, laps (number of laps completed), time (time taken to finish the race. if this begins with + then the value is race leader's time + value given), milliseconds (total time taken in milliseconds), fastestLap (lap number of fastest lap), rank (rank of fastest lap), fastestLapTime, fastestLapSpeed (top speed of fastest lap), statusID (status of driver)
        - seasons - This table contains the year and a url link of the Wikipedia page corresponding to that season for more information
        - sprint_results - This table contains information about results of sprint races during the race week. Columns: resultID, raceID, driverID, constructorID, number (car number), grid (position at the start of the race), position (at the end of the race), points, laps (number of laps completed), time (time taken to finish the race. if this begins with + then the value is race leader's time + value given), milliseconds (total time taken in milliseconds), fastestLap (lap number of fastest lap), fastestLapTime, statusID (status of driver)
        - status - This table contains the mapping for a description for each statusID. It describes the status of a driver for a particular race. Columns: statusID, status

        Interconnections:
        Columns like driverID, constructorID, circuitID, raceID, and statusID are used to interconnect the tables.

        Instructions:
        - Write only the SQL query and nothing else. Don't wrap the text in anything, not even backticks.
        - Pay attention to use date('now') function to get the current date when required
        - Ensure SQL queries are concise and efficient, select unique whenever required
        - Ensure you query for only existing columns
        - Properly handle joins between tables to ensure accurate data retrieval. Join on the required IDs whenever asking for a number of occurences of a particular event. 
        - When using COUNT() with table joins, make sure to use COUNT(DISTINCT column_name)                                               
        - The driver that get position 1 in the race is the winner and so on.
        - If the year or date is involved while getting the response, join with the races table and use the year or date column. RESULTS TABLE DOESNT HAVE YEAR DETAILS
        - A driver/constructor wins the championship if they have the most points in the standings at the end of the year
        - Pole position refers to qualifying first, or starting the race first on the grid
        - If a driver has finished the race in the top 3 then they are on the podium
        - Did not Finish of DNF refers to position='\\N' in the results table. DO NOT USE THE WORD 'NULL' or NULL
        - Status types available - Finished, Disqualified, Accident, Collision, Engine, Gearbox, Transmission, Clutch, Hydraulics, Electrical, +1 Lap, +2 Laps, +3 Laps, +4 Laps, +5 Laps, +6 Laps, +7 Laps, +8 Laps, +9 Laps, Spun off, Radiator, Suspension, Brakes, Differential, Overheating, Mechanical, Tyre, Driver Seat, Puncture, Driveshaft, Retired, Fuel pressure, Front wing, Water pressure, Refuelling, Wheel, Throttle, Steering, Technical, Electronics, Broken wing, Heat shield fire, Exhaust, Oil leak, +11 Laps, Wheel rim, Water leak, Fuel pump, Track rod, +17 Laps, Oil pressure, +42 Laps, +13 Laps, Withdrew, +12 Laps, Engine fire, Engine misfire, +26 Laps, Tyre puncture, Out of fuel, Wheel nut, Not classified, Pneumatics, Handling, Rear wing, Fire, Wheel bearing, Physical, Fuel system, Oil line, Fuel rig, Launch control, Injured, Fuel, Power loss, Vibrations, 107% Rule, Safety, Drivetrain, Ignition, Did not qualify, Injury, Chassis, Battery, Stalled, Halfshaft, Crankshaft, +10 Laps, Safety concerns, Not restarted, Alternator, Underweight, Safety belt, Oil pump, Fuel leak, Excluded, Did not prequalify, Injection, Distributor, Driver unwell, Turbo, CV joint, Water pump, Fatal accident, Spark plugs, Fuel pipe, Eye injury, Oil pipe, Axle, Water pipe, +14 Laps, +15 Laps, +25 Laps, +18 Laps, +22 Laps, +16 Laps, +24 Laps, +29 Laps, +23 Laps, +21 Laps, Magneto, +44 Laps, +30 Laps, +19 Laps, +46 Laps, Supercharger, +20 Laps, Collision damage, Power Unit, ERS, +49 Laps, +38 Laps, Brake duct, Seat, Damage, Debris, Illness, Undertray, Cooling system
        - For a crash include all these status types - Accident, Collision, Spun off, Collision damage, Fatal accident
        - For points scored in a season, use the points column for the last race of the season in the driver's/constructors standings

        Take conversation history into account.
        Conversation history: {chat_history}

        Below are some example questions and corresponding SQL queries for better understanding. Take this as reference and use similar queries:

        Human: How many times has Lewis won the championship?
        AI: SELECT COUNT(*) AS championship_wins FROM (SELECT ds.driverID, r.year FROM driver_standings ds JOIN races r ON ds.raceID = r.raceID JOIN drivers d ON ds.driverID = d.driverID WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton' AND ds.position = 1 AND r.round = (SELECT MAX(ra.round) FROM races ra WHERE ra.year = r.year) GROUP BY r.year) AS final_standings;
        Human: What was the position of Mercedes in the 2020 British Grand Prix?
        AI: SELECT cs.position FROM constructor_standings cs JOIN constructors c ON cs.constructorID = c.constructorID JOIN races r ON cs.raceID = r.raceID WHERE r.year = 2020 AND r.name = 'British Grand Prix' AND c.name = 'Mercedes';
        Human: Which constructor had the most wins in the 2020 season?
        AI: SELECT c.name, COUNT(DISTINCT res.resultID) AS wins FROM results res JOIN constructors c ON res.constructorID = c.constructorID JOIN races r ON res.raceID = r.raceID WHERE r.year = 2020 AND res.positionOrder = 1 GROUP BY c.name ORDER BY wins DESC LIMIT 1;
        Human: Which teams did Lewis Hamilton race for?
        AI: SELECT DISTINCT c.name FROM results r JOIN drivers d ON r.driverID = d.driverID JOIN constructors c ON r.constructorID = c.constructorID WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton';
        Human: Which drivers have got pole positions for Ferrari?
        AI: SELECT DISTINCT d.forename, d.surname FROM qualifying q JOIN constructors c ON q.constructorID = c.constructorID JOIN drivers d ON q.driverID = d.driverID WHERE c.name = 'Ferrari' AND q.position = 1;
        Human: Which drivers qualified on pole and finished first in the race in 2008?
        AI: SELECT DISTINCT d.forename, d.surname FROM qualifying q JOIN results r ON q.raceID = r.raceID AND q.driverID = r.driverID JOIN drivers d ON q.driverID = d.driverID WHERE r.grid = 1 AND r.position = 1 AND q.raceID IN ( SELECT raceID FROM races WHERE year = 2008);
        Human: Which driver took the maximum number of races to get their first win?
        AI: WITH FirstWin AS (SELECT driverID, MIN(ra.date) AS first_win_date FROM results r JOIN races ra ON r.raceID = ra.raceID WHERE r.position = 1 GROUP BY driverID), RacesBeforeFirstWin AS (SELECT d.driverID, d.forename, d.surname, COUNT(DISTINCT ra.raceID) AS races_before_win FROM results r JOIN drivers d ON r.driverID = d.driverID JOIN races ra ON r.raceID = ra.raceID JOIN FirstWin fw ON r.driverID = fw.driverID WHERE ra.date < fw.first_win_date GROUP BY d.driverID, d.forename, d.surname) SELECT forename, surname, races_before_win FROM RacesBeforeFirstWin ORDER BY races_before_win DESC LIMIT 1;
        Human: How many pole positions does Lewis have?
        AI: SELECT COUNT(DISTINCT r.raceID) AS pole_positions FROM results res JOIN drivers d ON res.driverID = d.driverID JOIN races r ON res.raceID = r.raceID WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton' AND res.grid = 1;
        Human: How many podiums has Michael Schumacher got?
        AI: SELECT COUNT(DISTINCT r.raceID) AS podiums FROM results r JOIN drivers d ON r.driverID = d.driverID WHERE d.forename = 'Michael' AND d.surname = 'Schumacher'AND r.position IN (1,2,3);                                                                                        
        Human: Which driver has won the most number of races in any single season?
        AI: SELECT d.forename, d.surname, r.year, COUNT(DISTINCT res.resultID) AS wins FROM results res JOIN drivers d ON res.driverID = d.driverID JOIN races r ON res.raceID = r.raceID WHERE res.positionOrder = 1 GROUP BY d.forename, d.surname, r.year ORDER BY wins DESC LIMIT 1;
        Human: In which circuits has Lewis Hamilton never won a race?  
        AI: SELECT DISTINCT(c.name) AS circuit_name FROM circuits c LEFT JOIN (SELECT DISTINCT r.circuitID FROM results res JOIN races r ON res.raceID = r.raceID JOIN drivers d ON res.driverID = d.driverID WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton' AND res.positionOrder = 1) AS lh_wins ON c.circuitID = lh_wins.circuitID WHERE lh_wins.circuitID IS NULL;                                                                                            
        Human: Which driver has participated in the most races without having won a race?
        AI:SELECT d.forename, d.surname, COUNT(DISTINCT res.raceID) AS race_count FROM drivers d JOIN results res ON d.driverID = res.driverID LEFT JOIN ( SELECT DISTINCT driverID FROM results WHERE positionOrder = 1 ) AS winners ON d.driverID = winners.driverID WHERE winners.driverID IS NULL GROUP BY d.forename, d.surname ORDER BY race_count DESC LIMIT 1;
        Human: How many races did Max Verstappen not finish?                                           
        AI:SELECT COUNT(DISTINCT raceID) AS races_not_finished FROM results WHERE driverID = (SELECT driverID FROM drivers WHERE forename = 'Max' AND surname = 'Verstappen') AND position='\\N';
        Human:How many races did it take Lewis to get his first win?
        AI: WITH FirstWin AS (SELECT driverID, MIN(ra.date) AS first_win_date FROM results JOIN races AS ra ON results.raceID = ra.raceID WHERE results.position = 1 GROUP BY driverID), RacesBeforeFirstWin AS (SELECT d.driverID, d.forename, d.surname, COUNT(DISTINCT ra.raceID) AS races_before_win FROM results JOIN drivers AS d ON results.driverID = d.driverID JOIN races AS ra ON results.raceID = ra.raceID JOIN FirstWin AS fw ON results.driverID = fw.driverID WHERE ra.date < fw.first_win_date GROUP BY d.driverID, d.forename, d.surname) SELECT forename, surname, races_before_win FROM RacesBeforeFirstWin WHERE driverID = (SELECT driverID FROM drivers WHERE forename = 'Lewis' AND surname = 'Hamilton');
        Human: How many points did Lando Norris score in 2023?                       
        AI: SELECT DISTINCT(ds.points) AS total_points FROM driver_standings ds JOIN drivers d ON ds.driverID = d.driverID JOIN races r ON ds.raceID = r.raceID WHERE d.forename = 'Lando' AND d.surname = 'Norris' AND r.year = 2023 AND r.date = (SELECT MAX(date) FROM races WHERE year = 2023);


        Question: {question}
        SQL Query:
        """    
    
    prompt= ChatPromptTemplate.from_template(template)

    llm = ChatGoogleGenerativeAI(model="gemini-pro")

    return (
        prompt | llm | StrOutputParser()
    )

def get_response(user_query:str, db: SQLDatabase):
    sql_chain = get_sql_chain()
    execute_query= QuerySQLDataBaseTool(db=db)
    template = """
        Given the following user question, corresponding SQL query, and SQL result, awrite a natural language response.
        If error, please respond appropriately.

        Conversation history: {chat_history}
        Question: {question}
        SQL Query: {query}
        SQL Result: {result}
        Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatGoogleGenerativeAI(model="gemini-pro")

    rephrase_answer = prompt | llm | StrOutputParser()

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            result=lambda d: execute_query(d["query"].strip("```sql\n")))
        | rephrase_answer
    )

    return (chain.invoke({
        'chat_history': st.session_state.chat_history,
        'question': user_query
    }))
    

#Loading database
db = SQLDatabase.from_uri("sqlite:///database.sqlite")


if "chat_history" not in st.session_state:
    st.session_state.chat_history=[
        AIMessage(content="Hey there! Ask me a question. ")
    ]


load_dotenv()

st.set_page_config(page_title="F1 Factbot",page_icon=":speech_balloon:")

st.title("F1 Factbot")

with st.sidebar:
    st.image("f1-logo.png")
    st.write("Ask questions about drivers, constructors or tracks!")
    st.write("Try to keep the question clear and simple as far as possible. If error, try asking again :)")
    st.caption("Natural language to SQL bot built using Gemini API \n\n <a href='https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020' target='_blank'>Dataset</a>", unsafe_allow_html=True)

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)


user_query = st.chat_input("Type a message...")

if user_query is not None and user_query.strip() !="":
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        response = get_response(user_query, db)
        st.markdown(response)
    
    st.session_state.chat_history.append(AIMessage(content=response))
