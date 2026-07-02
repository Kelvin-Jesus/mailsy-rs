//! Core application code for the `mailghost` command-line client.

mod account;
mod app;
mod cli;
mod home;

pub use app::run;
pub use cli::Cli;
