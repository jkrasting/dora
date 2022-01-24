openssl req -x509 -nodes -days 730 -newkey rsa:2048 -keyout key.pem -out cert.pem -config req.conf -extensions 'v3_req'

See:  https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl

See: https://support.citrix.com/article/CTX135602
