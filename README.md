# FBSR Pöntunarkerfi

Þetta kerfi byggir á python/flask bakenda og tveimur react bakendum, einum fyrir pöntunar síðuna og öðrum fyrir "admin" hluta kerfisins.
Smíðað utan um PostgreSQL gagnagrunn og notar einnig Redis til að tala milli bakenda og process sem sér um að senda tölvupósta. Það má eflaust nota pub/sub fítusa í PostgreSQL til að fjarlægja Redis dependencyið.

Til að keyra upp development server:
 

    export FLASK_APP=backend
    flask run
    
    cd frontend
    npm start
    
    cd admin
    npm start
