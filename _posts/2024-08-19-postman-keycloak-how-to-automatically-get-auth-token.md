---
title: Postman + Keycloak – How to automatically get the authentication token
categories:
  - development-tools
comments: true
---
It often happens that you have to test REST services that require authentication, perhaps with keycloak. With Postman you can automatically get the access token before making each REST call. Let's see how
## What is Postman
If you develop backends you will surely know what Postman is, if not (or if you are new to the industry), allow me to introduce it to you:

Postman is (to put it very simply) a platform for building, testing and cataloging APIs. It can be downloaded for free from the [official website](https://translate.google.com/website?sl=it&tl=en&hl=en&client=webapp&u=https://www.postman.com/ "official site") and also has paid plans for teams and more complex projects, but the free version is fine for us.

One of the most convenient features is the possibility of cataloging all our requests in what are called **collections** , which are a concept very similar to directories.

![Postman Collections](https://github.com/basteez/basteez.github.io/blob/main/assets/img/postman-keycloak/01.png)
**Each collection can be configured in its own way and this is exactly what we are going to do to automatically obtain the keycloak** authentication token .

## Pre-request script
Pre-request scripts are, in fact, JavaScript scripts that are executed before a request. They can be inserted in two different places: within the single request or in the collection; the advantage of doing it in the collection is that in this way all requests within it will automatically execute the script.

We then open our collection and in the **Pre-request Script** tab we add the following code, obviously being careful to make the appropriate substitutions in the first part with the variables:

```javascript
var client_id = "your keycloak client_id";
var client_secret = "your keycloak secret";
var server_url = "keycloak auth url";
var realm = "keycloak realm";
var username = "username";
var password = "password";

var token_endpoint = server_url + "/auth/realms/" + realm + "/protocol/openid-connect/token";

var details = {
   "grant_type" : "password",
   "username": username,
   "password": password
}

var formBody = [];

for (var property in details) {
    var encodedKey = encodeURIComponent(property);
    var encodedValue = encodeURIComponent(details[property]);
    formBody.push(encodedKey + "=" + encodedValue);
}

formBody = formBody.join("&");

pm.sendRequest({
   url: token_endpoint,
   method: 'POST',
   header: {
       'Content-Type': 'application/x-www-form-urlencoded',

       'Authorization' :'Basic ' + btoa(client_id+":"+client_secret)
         },
     body: formBody
}, function(err, response) {
    const jsonResponse = response.json();
    console.log(jsonResponse.access_token);
    pm.collectionVariables.set("access-token", jsonResponse.access_token);
});
```
Then we open the **Authorization** tab and set the type field as _Bearer Token_ and the Token field as`{{access-token}}`
![Postman Authorization tab](https://github.com/basteez/basteez.github.io/blob/main/assets/img/postman-keycloak/02.png)
## Single request

At this point the last thing to do is to set the individual requests so that they inherit the authorization mode from the collection. To do this we open our request and in the Authorization tab we set the Type field as _Inherit auth from parent_ .

![Postman Request](https://github.com/basteez/basteez.github.io/blob/main/assets/img/postman-keycloak/03.png)
At this point, every time we start the request, Postman will automatically contact the keycloak SSO to obtain the authentication token before making the request itself.

## Conclusions

**We have seen how to automatically obtain the keycloak** authentication token with **Postman** . Did you already know this method? Do you know any other interesting uses of pre-request scripts? Let me know in the comments
