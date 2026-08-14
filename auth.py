use std::collections::HashMap;
use std::io;

fn main() -> io::Result<()> {
    let mut users: HashMap<String, String> = HashMap::new();
    users.insert("admin".to_string(), "1234".to_string());
    users.insert("abhinav".to_string(), "password".to_string());

    println!("Username: ");
    let mut username = String::new();
    io::stdin().read_line(&mut username)?;
    let username = username.trim().to_string();

    println!("Password: ");
    let mut password = String::new();
    io::stdin().read_line(&mut password)?;
    let password = password.trim().to_string();

    if let Some(pwd) = users.get(&username) {
        if pwd == &password {
            println!("Login successful!");
        } else {
            println!("Invalid username or password.");
        }
    } else {
        println!("Invalid username or password.");
    }

    Ok(())
}