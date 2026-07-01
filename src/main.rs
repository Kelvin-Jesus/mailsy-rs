use std::fs;
use std::path::PathBuf;

use chrono::{DateTime, Utc};
use clap::{Parser, Subcommand};
use ephemeral_email::{ProviderType, TempMail};
use serde::{Deserialize, Serialize};

#[derive(Parser)]
#[command(
    name = "mailsy",
    version,
    about = "Quickly generate a disposable email straight from terminal"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate a new email
    G,
    /// Fetch messages from the inbox
    M,
    /// Delete account
    D,
    /// Show details of the account
    Me,
}

#[derive(Serialize, Deserialize)]
struct Account {
    email: String,
    created_at: DateTime<Utc>,
}

fn account_path() -> PathBuf {
    let dir = dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("mailsy");
    fs::create_dir_all(&dir).ok();
    dir.join("account.json")
}

fn load_account() -> Option<Account> {
    let path = account_path();
    if !path.exists() {
        return None;
    }
    let data = fs::read_to_string(&path).ok()?;
    serde_json::from_str(&data).ok()
}

fn save_account(account: &Account) -> bool {
    let path = account_path();
    let data = serde_json::to_string_pretty(account).unwrap();
    fs::write(path, data).is_ok()
}

fn delete_account_file() -> bool {
    let path = account_path();
    if path.exists() {
        fs::remove_file(path).is_ok()
    } else {
        true
    }
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::G => cmd_generate().await,
        Commands::M => cmd_messages().await,
        Commands::D => cmd_delete().await,
        Commands::Me => cmd_me(),
    }
}

async fn cmd_generate() {
    if load_account().is_some() {
        eprintln!("Account already exists. Delete it first with `mailsy d`.");
        return;
    }

    let inbox = TempMail::new()
        .provider_type(ProviderType::MailTm)
        .create_inbox()
        .await;

    let inbox = match inbox {
        Ok(i) => i,
        Err(e) => {
            eprintln!("Error creating inbox: {e}");
            return;
        }
    };

    let email = inbox.get_email_address().to_string();
    let account = Account {
        email: email.clone(),
        created_at: Utc::now(),
    };

    if save_account(&account) {
        println!("{email}");
    } else {
        eprintln!("Failed to save account.");
    }
}

async fn cmd_messages() {
    let account = match load_account() {
        Some(a) => a,
        None => {
            eprintln!("Account not created yet. Run `mailsy g` first.");
            return;
        }
    };

    let name = account.email.split('@').next().unwrap_or("");
    let inbox = TempMail::new()
        .provider_type(ProviderType::MailTm)
        .name(name)
        .create_inbox()
        .await;

    let inbox = match inbox {
        Ok(i) => i,
        Err(e) => {
            eprintln!("Error connecting to inbox: {e}");
            return;
        }
    };

    let messages = match inbox.get_messages().await {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Error fetching messages: {e}");
            return;
        }
    };

    if messages.is_empty() {
        println!("No messages.");
        return;
    }

    println!("Messages:");
    for (i, msg) in messages.iter().enumerate() {
        println!("  {}. {} - from {}", i + 1, msg.subject, msg.from);
    }

    print!("\nEnter message number to open (or Enter to skip): ");
    use std::io::{self, Write};
    io::stdout().flush().ok();

    let mut input = String::new();
    io::stdin().read_line(&mut input).ok();

    if let Ok(num) = input.trim().parse::<usize>() {
        if num >= 1 && num <= messages.len() {
            let msg = &messages[num - 1];
            if !msg.body.is_empty() {
                let tmp = std::env::temp_dir().join("mailsy_email.html");
                fs::write(&tmp, &msg.body).ok();
                open::that(&tmp).ok();
            } else {
                println!("No HTML content found.");
            }
        }
    }
}

async fn cmd_delete() {
    let account = match load_account() {
        Some(a) => a,
        None => {
            eprintln!("Account not created yet.");
            return;
        }
    };

    let name = account.email.split('@').next().unwrap_or("");
    let inbox = TempMail::new()
        .provider_type(ProviderType::MailTm)
        .name(name)
        .create_inbox()
        .await;

    delete_account_file();

    match inbox {
        Ok(_) => println!("Account deleted."),
        Err(_) => println!("Account data cleared."),
    }
}

fn cmd_me() {
    match load_account() {
        Some(account) => {
            println!("  Email: {}", account.email);
            println!(
                "  createdAt: {}",
                account.created_at.format("%d/%m/%Y, %H:%M:%S")
            );
        }
        None => {
            eprintln!("Account not created yet. Run `mailsy g` first.");
        }
    }
}
