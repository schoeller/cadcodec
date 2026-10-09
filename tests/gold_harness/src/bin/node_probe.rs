use opencadcodec::objects::{AssocConstraintNodeData, ObjectType};
use opencadcodec::DwgReader;

fn dump(path: &str) {
    let mut reader = DwgReader::from_file(path).unwrap();
    let document = reader.read().unwrap();
    println!("== {path}");
    for (h, obj) in document.objects.iter() {
        if let opencadcodec::objects::ObjectType::Associative(a) = obj {
            if let opencadcodec::objects::AssociativeData::ConstraintGroup(g) = &a.data {
                if g.nodes.is_empty() && g.nodes_wire_main.is_none() {
                    continue;
                }
                println!(
                    "group h={} v={} nodes={} wire_names={:?} wire_main={}B wire_text={}B wire_handles={}B",
                    h.value(),
                    g.version,
                    g.nodes.len(),
                    g.nodes_wire_names,
                    g.nodes_wire_main.as_ref().map(|b| b.len()).unwrap_or(0),
                    g.nodes_wire_text.as_ref().map(|b| b.len()).unwrap_or(0),
                    g.nodes_wire_handles.as_ref().map(|b| b.len()).unwrap_or(0),
                );
                for (i, n) in g.nodes.iter().enumerate() {
                    let d = match &n.data {
                        AssocConstraintNodeData::None => "None".to_string(),
                        other => format!("{:?}", other),
                    };
                    println!(
                        "  node[{i}] id={} status={} conns={:?} class={:?} data={}",
                        n.node_id, n.status, n.connections, n.class_name, &d[..d.len().min(60)]
                    );
                }
                if let Some(bytes) = &g.nodes_wire_main {
                    print!("  main[0..48]: ");
                    for b in bytes.iter().take(48) {
                        print!("{:08b} ", b);
                    }
                    println!();
                    print!("  main hex: ");
                    for b in bytes.iter().take(32) {
                        print!("{:02x}", b);
                    }
                    println!();
                }
            }
        }
    }
}

fn main() {
    for p in std::env::args().skip(1) {
        dump(&p);
    }
}
