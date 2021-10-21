# FBSR Pöntunarkerfi

Þetta kerfi byggir á python/flask bakenda og tveimur react bakendum, einum fyrir pöntunar síðuna og öðrum fyrir "admin" hluta kerfisins.
Smíðað utan um PostgreSQL gagnagrunn.

Til að keyra upp development server:

    # Start PostgreSQL

    export FLASK_APP=backend
    flask run
    
    cd frontend
    npm start
    
    cd admin
    npm start
