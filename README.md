# Flask Web Application for CineRate

## Purpose

CineRate is a web-based movie recommendation system that allows users to:

- Create a personal account
- Upload their viewing history or rating data (.csv or manual input)
- Receive **personalized movie recommendations**
- Visualize their genre preferences and rating trends
- Share results with friends for collaborative recommendations

---

## Design and Features

- Developed using the **Flask** web framework
- Follows the MVC pattern using **Jinja2**, **WTForms**, and **SQLAlchemy**
- Implements user authentication, session handling, and persistent storage
- Core functionalities include user login, movie rating, trend visualization, and sharing

---


## Group Members

| UWA ID   | Name            | GitHub Username   |
|----------|-----------------|-------------------|
| 23371813 | Frank Fu        | FRANKAYFU         |
| 24084355 | WEIMAN GAO      | WeimanGao         |
| 23831346 | Jasper Chadwick | SwordOfTheNebulae |
| 24214099 | Lucan McDonald  | PiesOnTues        |

---

## How to Launch the Application

1. Clone the repository:
   ```bash
   git clone https://github.com/SwordOfTheNebulae/cits3403-project.git
   cd flask
2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate         # Mac/Linux
   .\venv\Scripts\activate          # Windows
3. Install dependencies
   ```bash
   pip install -r requirements.txt
4. Run flask
   ```bash
   python app.py  # Default running address: http://127.0.0.1:5000/

---

## How to Run the Tests

1. Ensure venv is active
2. Run tests
   ```bash
   pytest tests/

---

## Project Structure

```bash
.
├── flask/                           # Main application package 
│   ├── app.py                     # Flask application script 
│   ├── config.py                  # Application configuration settings 
│   ├── create_app.py              # Application factory function
│   ├── data/                      # Data storage or processing scripts 
│   ├── instance/                  # Instance-specific files
│   ├── migrations/                # Database migration scripts 
│   │   └── versions/              # Versioned migration files 
│   ├── models/                    # SQLAlchemy model definitions 
│   ├── routes/                    # Route (view) functions
│   ├── static/                    # Static files (CSS, JS, images, fonts) 
│   │   ├── css/                   
│   │   ├── font/                  
│   │   ├── images/               
│   │   └── js/                    
│   ├── templates/                 # Jinja2 HTML templates 
│   └── utils/                     # Utility/helper functions 
├── media/                         # Uploaded media files 
│   ├── comment/                   
│   ├── movie_cover/               
│   └── movie_uploads/             
├── tests/                         # Test scripts and cases 
├── .gitignore   
├── requirements.txt               # Python package dependencies 
└── README.md                      # Project documentation 
```

---

## Files Ignored from Git | `.gitignore` 

To keep the repository clean and avoid uploading sensitive or unnecessary files, the project includes a `.gitignore` file that excludes the following:

- Python cache files (`__pycache__/`, `*.pyc`)
- Flask environment files (`.flaskenv`, `.env`)
- Virtual environment folder (`/venv/`)
- IDE and system files (`.vscode/`, `.DS_Store`)

