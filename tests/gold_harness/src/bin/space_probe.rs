use opencadcodec::objects::ObjectType;
use opencadcodec::{DwgReader, Handle};

fn dump(path: &str) {
    let mut reader = DwgReader::from_file(path).unwrap();
    let document = reader.read().unwrap();
    println!("== {path}");
    for record in document.block_records.iter() {
        if !(record.name == "*Model_Space" || record.is_model_space()) {
            continue;
        }
        println!(
            "record {} ({}) entities={}",
            record.name,
            record.handle.value(),
            record.entity_handles.len()
        );
        for h in &record.entity_handles {
            let what = match document.objects.get(h) {
                Some(obj) => {
                    let s = format!("{:?}", obj);
                    s[..s.len().min(34)].to_string()
                }
                None => match document.get_entity(*h) {
                    Some(e) => {
                        let s = format!("{:?}", e);
                        s[..s.len().min(34)].to_string()
                    }
                    None => "NOT FOUND".to_string(),
                },
            };
            println!("  entity h={} -> {}", h.value(), what);
        }
    }
    for (h, obj) in document.objects.iter() {
        if let ObjectType::ClassObject(c) = obj {
            let d = format!("{:?}", c.data);
            if d.contains("SectionViewStyle") || d.contains("DetailViewStyle") {
                println!(
                    "object h={} owner={} reactors={} data={}",
                    h.value(),
                    c.owner.value(),
                    c.reactors.len(),
                    &d[..d.len().min(40)]
                );
            }
        }
    }
    let _ = Handle::NULL;
}

fn main() {
    for p in std::env::args().skip(1) {
        dump(&p);
    }
}
