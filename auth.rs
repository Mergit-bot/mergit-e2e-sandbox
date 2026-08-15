use bcrypt::{hash, verify};
use jsonwebtoken::{encode, decode, Header, EncodingKey, DecodingKey, Validation};
use std::collections::HashMap;

struct Auth {
    users: HashMap<String, String>,
}

impl Auth {
    fn new() -> Self {
        Auth {
            users: HashMap::new(),
        }
    }

    fn register(&mut self, username: String, password: String) {
        let hashed_password = hash(password, 12).unwrap();
        self.users.insert(username, hashed_password);
    }

    fn login(&self, username: String, password: String) -> bool {
        if let Some(hashed_password) = self.users.get(&username) {
            verify(password, hashed_password).unwrap()
        } else {
            false
        }
    }

    fn generate_token(&self, username: String) -> String {
        let claims = Claims {
            sub: username,
            exp: 100000,
        };
        encode(&claims, &EncodingKey::from_secret("secret_key"), &Header::default()).unwrap()
    }

    fn verify_token(&self, token: String) -> bool {
        let token_data = decode::<Claims>(&token, &DecodingKey::from_secret("secret_key"), &Validation::default()).unwrap();
        token_data.claims.sub == self.users.keys().cloned().collect::<Vec<String>>().join(",")
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
}

fn main() {
    let mut auth = Auth::new();
    auth.register("admin".to_string(), "1234".to_string());
    auth.register("abhinav".to_string(), "password".to_string());

    let username = "admin".to_string();
    let password = "1234".to_string();
    if auth.login(username.clone(), password) {
        println!("Login successful!");
        let token = auth.generate_token(username);
        if auth.verify_token(token) {
            println!("Token is valid.");
        } else {
            println!("Token is invalid.");
        }
    } else {
        println!("Invalid username or password.");
    }
}