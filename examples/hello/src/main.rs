// Minimal std-only HTTP server for the celaut packer dogfood reference service.
//
// Deliberately dependency-free: no external crates means no crate downloads or
// Cargo.lock resolution at build time, which keeps the static musl binary
// byte-for-byte reproducible across builds (a prerequisite for a deterministic
// celaut service-id).
//
// Listens on 0.0.0.0:8080. GET /health -> "ok"; anything else -> a hello body.
use std::io::{Read, Write};
use std::net::TcpListener;

fn main() {
    let listener = TcpListener::bind("0.0.0.0:8080").expect("bind 0.0.0.0:8080");
    for stream in listener.incoming() {
        let mut sock = match stream {
            Ok(s) => s,
            Err(_) => continue,
        };
        let mut buf = [0u8; 1024];
        let n = sock.read(&mut buf).unwrap_or(0);
        let req = String::from_utf8_lossy(&buf[..n]);
        let path = req.split_whitespace().nth(1).unwrap_or("/");

        let body: &str = if path.starts_with("/health") {
            "ok"
        } else {
            "hello from the celaut rust reference service\n"
        };
        let resp = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\
             Content-Length: {}\r\nConnection: close\r\n\r\n{}",
            body.len(),
            body
        );
        let _ = sock.write_all(resp.as_bytes());
    }
}
