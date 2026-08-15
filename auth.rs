use std::collections::HashMap;
use std::io;

fn main() {
    let mut users: HashMap<String, String> = HashMap::new();
    users.insert("admin".to_string(), "1234".to_string());
    users.insert("abhinav".to_string(), "password".to_string());

    println!("Enter your username:");
    let mut username = String::new();
    io::stdin().read_line(&mut username).expect("Failed to read line");
    let username = username.trim();

    println!("Enter your password:");
    let mut password = String::new();
    io::stdin().read_line(&mut password).expect("Failed to read line");
    let password = password.trim();

    if let Some(stored_password) = users.get(username) {
        if stored_password == password {
            println!("Login successful!");
        } else {
            println!("Invalid username or password.");
        }
    } else {
        println!("Invalid username or password.");
    }
}
