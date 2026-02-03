// expressions.rs
//
// Copyright (c) 2025 Naufan Rusyda Faikar
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-License-Identifier: AGPL-3.0-or-later

#![allow(clippy::unused_unit)]
use polars::chunked_array::builder::list::ListStringChunkedBuilder;
use polars::prelude::*;
use pyo3_polars::derive::polars_expr;
use rand::Rng;
use serde::Deserialize;
use std::fmt::Write;

fn list_string_output(_: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(
        "".into(),
        DataType::List(Box::new(DataType::String)),
    ))
}

fn is_vowel(c: char) -> bool {
    matches!(c.to_ascii_lowercase(), 'a' | 'e' | 'i' | 'o' | 'u')
}

fn pig_latin_word(word: &str) -> String {
    if word.is_empty() {
        return String::new();
    }

    // Handle punctuation
    let (word_content, punctuation) =
    if let Some(last_char) = word.chars().last() {
        if last_char.is_ascii_punctuation() {
            (&word[0..word.len() - 1], Some(last_char))
        } else {
            (word, None)
        }
    } else {
        (word, None)
    };

    // Find the end of the initial consonant cluster
    let mut consonant_cluster_end = 0;
    if !is_vowel(word_content.chars().next().unwrap()) {
        for (i, c) in word_content.chars().enumerate() {
            if is_vowel(c) {
                consonant_cluster_end = i;
                break;
            }
            // If the word has no vowels, treat it as a special case
            if i == word_content.len() - 1 {
                consonant_cluster_end = word_content.len();
            }
        }
    }

    let result =
    if consonant_cluster_end == 0 {
        // Vowel starts the word, so just add "way"
        format!("{}way", word_content)
    } else {
        // Consonant cluster is moved to the end with "ay"
        let (consonant_cluster, rest_of_word) = word_content.split_at(consonant_cluster_end);

        let mut pig_latin_word_content = format!("{}{}{}", rest_of_word, consonant_cluster, "ay");

        // Handle capitalization
        if word_content.chars().next().unwrap().is_ascii_uppercase() {
            let first_char = pig_latin_word_content.chars().next().unwrap().to_ascii_uppercase();
            pig_latin_word_content.replace_range(..1, &first_char.to_string());
        }

        pig_latin_word_content
    };

    // Add back punctuation if it existed
    if let Some(punc) = punctuation {
        format!("{}{}", result, punc)
    } else {
        result
    }
}

#[polars_expr(output_type=String)]
fn pig_latinnify(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let out: StringChunked = ca.apply_into_string_amortized(|value: &str, output: &mut String| {
        let translated_words: Vec<String> = value
            .split_whitespace()
            .map(|word| pig_latin_word(word))
            .collect();
        write!(output, "{}", translated_words.join(" ")).unwrap();
    });
    Ok(out.into_series())
}

#[derive(Deserialize)]
pub struct SplitByCharsKwargs {
    characters: String,
}

#[polars_expr(output_type=String)]
fn split_by_chars(inputs: &[Series], kwargs: SplitByCharsKwargs) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let SplitByCharsKwargs { characters } = kwargs;
    let mut all_results: Vec<String> = Vec::new();
    for value in ca.iter() {
        if let Some(s) = value {
            for part in s.split(|c: char| characters.contains(c)) {
                all_results.push(part.trim().to_string());
            }
        }
    }
    let out: StringChunked = all_results.iter().map(|s| Some(s.as_str())).collect::<StringChunked>();
    Ok(out.into_series())
}

#[polars_expr(output_type_func=list_string_output)]
fn split_by_lowercase_to_uppercase(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let mut builder = ListStringChunkedBuilder::new("".into(), ca.len(), 0);
    for opt_s in ca.into_iter() {
        match opt_s {
            None => builder.append_null(),
            Some(s) => {
                let mut parts: Vec<String> = Vec::new();
                let mut buffer = String::new();
                let mut chars = s.chars().peekable();
                while let Some(c) = chars.next() {
                    buffer.push(c);
                    if c.is_lowercase() {
                        if let Some(&next) = chars.peek() {
                            if next.is_uppercase() {
                                parts.push(std::mem::take(&mut buffer));
                            }
                        }
                    }
                }
                if !buffer.is_empty() {
                    parts.push(buffer);
                }
                builder.append_series(&Series::new("".into(), parts))?;
            }
        }
    }
    Ok(builder.finish().into_series())
}

#[polars_expr(output_type_func=list_string_output)]
fn split_by_uppercase_to_lowercase(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let mut builder = ListStringChunkedBuilder::new("".into(), ca.len(), 0);
    for opt_s in ca.into_iter() {
        match opt_s {
            None => builder.append_null(),
            Some(s) => {
                let mut parts: Vec<String> = Vec::new();
                let mut buffer = String::new();
                let mut chars = s.chars().peekable();
                while let Some(c) = chars.next() {
                    buffer.push(c);
                    if c.is_uppercase() {
                        if let Some(&next) = chars.peek() {
                            if next.is_lowercase() {
                                parts.push(std::mem::take(&mut buffer));
                            }
                        }
                    }
                }
                if !buffer.is_empty() {
                    parts.push(buffer);
                }
                builder.append_series(&Series::new("".into(), parts))?;
            }
        }
    }
    Ok(builder.finish().into_series())
}

#[polars_expr(output_type_func=list_string_output)]
fn split_by_digit_to_nondigit(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let mut builder = ListStringChunkedBuilder::new("".into(), ca.len(), 0);
    for opt_s in ca.into_iter() {
        match opt_s {
            None => builder.append_null(),
            Some(s) => {
                let mut parts: Vec<String> = Vec::new();
                let mut buffer = String::new();
                let mut chars = s.chars().peekable();
                while let Some(c) = chars.next() {
                    buffer.push(c);
                    if c.is_ascii_digit() {
                        if let Some(&next) = chars.peek() {
                            if !next.is_ascii_digit() {
                                parts.push(std::mem::take(&mut buffer));
                            }
                        }
                    }
                }
                if !buffer.is_empty() {
                    parts.push(buffer);
                }
                builder.append_series(&Series::new("".into(), parts))?;
            }
        }
    }
    Ok(builder.finish().into_series())
}

#[polars_expr(output_type_func=list_string_output)]
fn split_by_nondigit_to_digit(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let mut builder = ListStringChunkedBuilder::new("".into(), ca.len(), 0);
    for opt_s in ca.into_iter() {
        match opt_s {
            None => builder.append_null(),
            Some(s) => {
                let mut parts: Vec<String> = Vec::new();
                let mut buffer = String::new();
                let mut chars = s.chars().peekable();
                while let Some(c) = chars.next() {
                    buffer.push(c);
                    if !c.is_ascii_digit() {
                        if let Some(&next) = chars.peek() {
                            if next.is_ascii_digit() {
                                parts.push(std::mem::take(&mut buffer));
                            }
                        }
                    }
                }
                if !buffer.is_empty() {
                    parts.push(buffer);
                }
                builder.append_series(&Series::new("".into(), parts))?;
            }
        }
    }
    Ok(builder.finish().into_series())
}

#[polars_expr(output_type=String)]
fn to_sentence_case(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let out: StringChunked = ca.apply_into_string_amortized(|value: &str, output: &mut String| {
        let mut capitalize_next = true;
        let mut last_char_was_lowercase = false;
        let mut last_char_was_punctuation = false;

        for c in value.chars() {
            if c.is_alphabetic() {
                // Insert a space if the last character was lowercase and the current is uppercase.
                let should_insert_space = last_char_was_lowercase && c.is_uppercase();
                if should_insert_space {
                    output.push(' ');
                }

                // Apply capitalization rules
                if capitalize_next {
                    output.extend(c.to_uppercase());
                } else {
                    output.extend(c.to_lowercase());
                }

                // Update state variables for the next iteration.
                capitalize_next = false;
                last_char_was_lowercase = c.is_lowercase();
                last_char_was_punctuation = false;
            }
            // It's a non-alphabetic character.
            else {
                output.push(c);

                if c == '.' || c == '!' || c == '?' {
                    last_char_was_punctuation = true;
                }
                // Capitalize the next letter if the last character was a sentence ender and this is a space.
                else if c.is_whitespace() && last_char_was_punctuation {
                    capitalize_next = true;
                    last_char_was_punctuation = false;
                }
                // For other characters like hyphens or underscores, do not capitalize the next letter.
                else {
                    capitalize_next = false;
                    last_char_was_punctuation = false;
                }
                last_char_was_lowercase = false;
            }
        }
    });
    Ok(out.into_series())
}

#[polars_expr(output_type=String)]
fn to_sponge_case(inputs: &[Series]) -> PolarsResult<Series> {
    let ca: &StringChunked = inputs[0].str()?;
    let mut rng = rand::rng();
    let out: StringChunked = ca.apply_into_string_amortized(|value: &str, output: &mut String| {
        for c in value.chars() {
            if c.is_alphabetic() {
                if rng.random_bool(0.5) {
                    output.extend(c.to_uppercase());
                } else {
                    output.extend(c.to_lowercase());
                }
            } else {
                output.push(c);
            }
        }
    });
    Ok(out.into_series())
}