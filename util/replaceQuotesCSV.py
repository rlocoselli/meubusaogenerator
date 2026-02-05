def replaceQuotes (file):
    with open(file, 'r') as f: 
        text = f.read()  
        
    converted_text = text.replace('"', "")
    
    with open(file, 'w') as f: 
        f.write(converted_text) 