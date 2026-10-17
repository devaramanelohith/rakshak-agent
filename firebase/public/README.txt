Intentionally empty: Firebase Hosting serves nothing statically and rewrites every path to the Cloud Run
service `rakshak` (see ../../firebase.json). WebSockets connect straight to the Cloud Run URL (web/common.js).
