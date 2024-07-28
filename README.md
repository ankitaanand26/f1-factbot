<h1>Formula 1 Factbot</h1>

<h2>Overview</h2>
<p>F1 Factbot is a natural language to SQL chatbot designed to answer questions about Formula 1 drivers, constructors, and tracks. It utilizes the Gemini API for generating SQL queries from user inputs and retrieves relevant data from a SQLite database containing historical Formula 1 data (Uptil midseason 2024).</p>

<p>I've always found it cool how the commentators spring up relevant facts during a race. They undoubtedly have a huge team behind it, but here's my small attempt to find answers for my endlessly random questions.</p>
  
<h2>Features</h2>
<ul>
    <li><strong>Natural Language Processing</strong>: Convert user questions into SQL queries.</li>
    <li><strong>Database Integration</strong>: Query a SQLite database with interconnected tables of Formula 1 data.</li>
    <li><strong>Interactive Interface</strong>: User-friendly chat interface built with Streamlit.</li>
    <li><strong>Error Handling</strong>: Responds appropriately to errors and provides suggestions for rephrasing questions</li>
    <li><strong>Memory</strong>: Remembers the conversation history for better contextual understanding.</li>
</ul>

<h2>Requirements</h2>
<p>To run this project, you need the following dependencies:</p>
<ul>
  <li>Python 3.7+</li>
  <li>Streamlit</li>
  <li>LangChain</li>
  <li>langchain-experimental</li>
  <li>langchain-google-genai</li>
  <li>SQLAlchemy</li>
  <li>Pandas</li>
</ul>
<p>You can install the required dependencies using:</p>
<pre><code>pip install -r requirements.txt</code></pre>

<h2>Usage</h2>
<ol>
    <li>Clone the repository:
        <pre><code>git clone https://github.com/ankitaanand26/f1-factbot.git</code></pre>
    </li>
    <li>Navigate to the project directory:
        <pre><code>cd f1-factbot</code></pre>
    </li>
    <li>Create a <code>.env</code> file with your environment variables:
        <pre><code>GOOGLE_API_KEY="YOUR_API_KEY"</code></pre>
    </li>
    <li>Run the Streamlit app:
        <pre><code>streamlit run app.py</code></pre>
    </li>
  
</ol>

<h2>Dataset</h2>
<a href="https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020">Kaggle Formula 1 Dataset</a>

