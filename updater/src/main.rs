
use std::fs::File;
use std::io::copy;
use std::process::{Command, Output};

use error_chain::error_chain;
use tempfile::Builder;

error_chain! {
     foreign_links {
         Io(std::io::Error);
         HttpRequest(reqwest::Error);
     }
}

#[tokio::main]
async fn download() -> Result<File> {
    let tmp_dir = Builder::new().prefix("update-file").tempdir()?;
    let _version = 236;
    let url: &str = "https://dkratzert.de/files/dsr/DSR-setup-236.exe";
    println!("Downloading setup file from: {}", url);
    let response = reqwest::get(url).await?;

    let mut dest: File = {
        let file_name: &str = response
            .url()
            .path_segments()
            .and_then(|segments| segments.last())
            .and_then(|name| if name.is_empty() { None } else { Some(name) })
            .unwrap_or("dsr-setup.exe");

        println!("file to download: '{}'", file_name);
        let fname = tmp_dir.path().join(file_name);
        println!("will be located under: {:?}", fname);
        File::create(fname)?
    };
    let content = response.text().await?;
    copy(&mut content.as_bytes(), &mut dest)?;
    Ok(dest)
}

fn main() {
    let result = download();
    let output: Output =
        if cfg!(target_os = "windows") {
            Command::new("cmd")
                .args(["/C", "foo"])
                .output()
                .expect("failed to execute process")
        } else {
            Command::new("sh")
                .arg("-c")
                .arg("bar")
                .output()
                .expect("failed to execute process")
        };

    match result {
        Ok(n)  => println!("n is {:#?}", n),
        Err(e) => println!("Error: {}", e),
    }

    let hello = String::from_utf8_lossy(&output.stdout);
    println!("{:}", hello);
    let hello2 = String::from_utf8_lossy(&output.stderr);
    println!("{:}", hello2);
}