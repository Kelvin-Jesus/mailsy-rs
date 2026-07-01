//! Core application code for the `mailsy` command-line client.

mod account;
mod app;
mod cli;

pub use app::run;
pub use cli::Cli;
