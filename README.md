# mailsy

`mailsy` is a small command-line client for creating and reading a disposable
email inbox from the terminal. It currently uses [Mail.tm](https://mail.tm/)
through the `ephemeral_email` crate.

## Features

- Create one disposable inbox.
- Print the current email address and creation time.
- List messages received by the inbox.
- Open the HTML body of a selected message in the default application.
- Delete the locally stored account.

## Installation

Requires a current Rust toolchain.

```sh
git clone git@github.com:Kelvin-Jesus/mailsy-rs.git
cd mailsy-rs
cargo install --path .
```

The `mailsy` binary is installed in Cargo's binary directory, normally
`~/.cargo/bin`.

To build without installing:

```sh
cargo build --release
./target/release/mailsy --help
```

## Usage

Create an inbox:

```sh
mailsy g
```

Show the active account:

```sh
mailsy me
```

List received messages and optionally open one:

```sh
mailsy m
```

Delete the locally stored account:

```sh
mailsy d
```

Run `mailsy --help` to see all available commands.

## Local data

The active account is stored as `mailsy/account.json` inside the operating
system's user configuration directory:

- macOS: `~/Library/Application Support/mailsy/account.json`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/mailsy/account.json`

When a message contains HTML, `mailsy m` writes it temporarily to
`mailsy_email.html` in the system temporary directory before opening it.

Deleting an account removes the local account file. Disposable inboxes and
their availability are controlled by the upstream provider.

## Development

```sh
cargo fmt --check
cargo check
cargo test
```

The project uses Rust 2021 and keeps `Cargo.lock` versioned so builds use the
same dependency resolution.

## Limitations

- Only one local account is supported at a time.
- Mail.tm is currently the only provider.
- The CLI displays message metadata and opens HTML bodies; it does not provide
  a full terminal mail reader.
- Disposable email should not be used for sensitive, permanent, or
  account-recovery communication.

## License

MIT
