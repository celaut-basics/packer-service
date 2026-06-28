use std::io::{Read, Write};
use std::net::TcpListener;

fn main() {
    let port = std::env::var("PORT").unwrap_or_else(|_| "50051".into());
    let listener = TcpListener::bind(format!("0.0.0.0:{port}")).expect("bind");
    for stream in listener.incoming() {
        if let Ok(mut s) = stream {
            let mut buf = [0u8; 1024];
            let _ = s.read(&mut buf);
            let _ = s.write_all(
                b"HTTP/1.1 200 OK\r\nContent-Length: 36\r\n\r\nhello from your rust celaut service\n",
            );
        }
    }
}
