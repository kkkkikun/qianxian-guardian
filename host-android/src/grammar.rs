//! GBNF 语法约束定义
//! 用于在端侧模型解码采样阶段，从数学上保证输出必须遵循 PLAN 协议格式或纯文本回复。

pub const PLAN_GBNF_GRAMMAR: &str = r#"
root ::= response

response ::= plain_reply | (rationale "\n" plan_block)

rationale ::= [^\n]+

plan_block ::= "PLAN{" ws "\"op\":" ws op_name ("," ws field)* ws "}"

op_name ::= "\"create\"" | "\"confirm\"" | "\"reschedule\"" | "\"cancel\"" | "\"add_people\"" | "\"set_bill\"" | "\"complete\"" | "\"draft_dunning\"" | "\"mark_paid\"" | "\"undo\"" | "\"clear\"" | "\"export\""

field ::= string_field

string_field ::= key_name ":" ws string_val

key_name ::= "\"activity\"" | "\"slot_day\"" | "\"slot_part\"" | "\"place\"" | "\"people\"" | "\"bill_total\"" | "\"id\"" | "\"text\"" | "\"who\"" | "\"amount\""

string_val ::= "\"" [^"\\]* "\""

ws ::= [ \t]*

plain_reply ::= [^\n]+ ("\n" [^\n]+)*
"#;
