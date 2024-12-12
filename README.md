# Certification Management System

## Overview

The Certification Management System is a web application designed to manage user certifications, track qualification progressions, and calculate points based on various qualifications. The system includes user authentication, an admin panel, and the ability to upload and approve certificates.

## Features

User authentication with secure password hashing.

Role-based access control (Admin and User).

Certificate upload and point calculation for qualifications.

Certificate approval and rejection by administrators.

Qualification progression management with point allocation.

Messaging system between users and administrators.

File handling for uploaded certificates.

## Installation
### Prerequisites

Python 3.8+

Flask

SQLAlchemy

psycopg2 or another compatible database driver

### Setup

1. Clone the repository:
``` bash
git clone https://github.com/
cd
```
2. Create a virtual environment and activate it:
``` bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install the dependencies:
``` bash
pip install -r requirements.txt
```
4. Set up environment variables:
Create a .env file in the root directory with the following variables:
``` bash
SECRET_KEY=your_secret_key
UPLOAD_FOLDER=path_to_upload_folder
DATABASE_URL=your_database_connection_string
```
5. Initialize the database:
```bash
flask db upgrade
```
6. Run the application:
```bash
flask run
```
7. Access the application at http://127.0.0.1:5000.

## Project Structure

app/: Core application code.

routes.py: Defines all application routes and views.

models.py: Database models for the application.

forms.py: Form definitions using Flask-WTF.

utils.py: Utility functions for authentication, point calculations, and more.

config.py: Configuration settings and constants.

## Usage
### User Roles
Admin: Can approve/reject certificates, manage users, and access admin-specific routes.

User: Can upload certificates, view pending and approved certificates, and manage personal qualifications.

### Points System
Points are calculated based on specific rules for each qualification. The system tracks:

Total points for each qualification.

Excess hours for qualifications that exceed minimum requirements.

Points used for progression.

### Messaging
Users can send messages to administrators through the /api/mensagens_usuario route. Admins can view all messages sent to them via the /api/mensagens route.

## API Endpoints
POST /api/mensagens_usuario: Send a message to the administrator.

GET /api/mensagens: Retrieve messages sent to the administrator (Admin only).

## Configuration
### Qualifications
The config.py file contains a list of supported qualifications and their point limits. Modify these as needed:
```bash
QUALIFICACOES = [
    "Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.",
    "Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.",
    "Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.",
    "Cursos de graduação e especialização realizados em instituição pública ou privada, reconhecida pelo MEC.",
    "Mestrado, doutorado e pós-doutorado realizados em instituição pública ou privada, reconhecida pelo MEC.",
    "Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.",
    "Participação em grupos, equipes, comissões e projetos especiais, no âmbito do Município do Recife, formalizados por ato oficial.",
    "Exercício de cargos comissionados e funções gratificadas, ocupados, exclusivamente, no âmbito do Poder Executivo Municipal."
]
```

## Testing
Run tests using:
```bash
pytest
```

## Future Enhancements
Add report generation for certificates and qualifications.

Integrate email notifications for certificate approval/rejection.

Enhance the admin dashboard with more insights and analytics.


## Contributing

1. Fork the repository.
2. Create a feature branch:
```bash
git checkout -b feature-name
```
3. Commit your changes:
```bash
git commit -m 'Add feature description'
```
4. Push to your fork:
```bash
git push origin feature-name
```

5. Create a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For questions or feedback, please contact [tn-junior@hotmail.com].


