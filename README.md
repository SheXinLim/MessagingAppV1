# INFO2222-Project

# Project Functionality Checklist

## Basic Functionality Requirements

- [x] **User Login (6 marks)**
  - [x] Users can log in with their username and password.
  - [x] Display the reason for login failure if the login attempt fails.

- [x] **Display Friend List (6 marks)**
  - [x] Show a list of all users the logged-in user is friends with upon successful login.

- [x] **Add Friends (6 marks)**
  - [x] Allow users to add friends by submitting another user’s username to the server.

- [x] **Friend Requests Management (6 marks)**
  - [x] Users can view a list of their friend requests (both sent and received).
  - [x] Users can approve or reject friend requests received from others.

- [ ] **Secure Chatroom Functionality (30 marks)**
  - [ ] Users can click on a friend to open a chatroom.
  - [ ] Ensure secure communication in the chatroom if both users are online and are friends.
  - [ ] Encrypt messages so the server cannot read them.
  - [ ] Use Message Authentication Code (MAC) to ensure message integrity.
  
- [ ] **Secure Message History (15 marks)**
  - [ ] Store message history securely encrypted on the server.
  - [ ] Display the message history when a user opens a chatroom session.
  - [ ] Use the user’s password to derive the key for encryption without the server knowing the password.

## Additional Criteria

- [x] **Secure Password Storage (6 marks)**
  - [x] Properly store passwords on the server using hash and salt.
  
- [ ] **HTTPS Communication (10 marks)**
  - [ ] Use HTTPS to secure communication between the client and server.
  - [ ] Ensure no browser warnings like “this site is not secure” appear.
  
- [ ] **Authenticated Requests (15 marks)**
  - [ ] Ensure all requests to the server are properly authenticated (e.g., using a session token/cookie).

## Total Marks: 100
