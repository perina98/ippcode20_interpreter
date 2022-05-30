<?php
/* Pomocné premenné */
$recursive = FALSE;
$parse_only = FALSE;
$int_only = FALSE;
$passed_cnt = 0;
$failed_cnt = 0;

/* Spracovanie argumentov testovacieho skriptu */
if ($argc > 1){
    foreach($argv as $arg){
        if($arg == "--help"){
            if($argc > 2){
                exit(10);
            } else {
                echo "Skript typu filtr (parse.php v jazyce PHP 7.4) načte ze standardního vstupu zdrojový kód v IPPcode20
                    , zkontroluje lexikální a syntaktickou správnost kódu a vypíše na standardní
                    výstup XML reprezentaci programu dle specifikace.\n";
                exit(0);
            }
        }
        elseif(preg_match('/^--directory=(\.){0,2}(\/*[a-zA-Z]*\d*\S*)*$/',$arg)){
            $dir = substr($arg,12);
            if (!is_dir($dir . '/')) {
                exit(11);
            }
        }
        elseif($arg == "--recursive"){
            $recursive = TRUE;
        }
        elseif(preg_match('/^--parse-script=(\.){0,2}(\/*[a-zA-Z]*\d*\.*)*$/',$arg)){
            $parser = substr($arg,15);
        }
        elseif(preg_match('/^--int-script=(\.){0,2}(\/*[a-zA-Z]*\d*\.*)*$/',$arg)){
            $interpreter = substr($arg,13);
        }
        elseif($arg == "--parse-only"){
            if(!$int_only){
                $parse_only = TRUE;
            } else {
                exit(10);
            }
        }
        elseif($arg == "--int-only"){
            if(!$parse_only){
                $int_only = TRUE;
            } else {
                exit(10);
            }
        }
        elseif(preg_match('/^--jexamxml=(\.){0,2}(\/*[a-zA-Z]*\d*\.*)*$/',$arg)){
            $jexaml = substr($arg,11);  
        }
        elseif($arg != "test.php") {
            exit(10); 
        }   
    }
} 


/* Funkcia použitá v prípade parse-only parametru
* $parser - názov alebo cesta k súboru parse.php
* $file - názov a cesta aktuálneho testu
* $current_file - názov aktuálneho testu bez prípony
* $rc - očakávaný návratový kód 
* $jexaml - názpv alebo cesta k súboru jexamxl
* $dir - názov aktuálnej zložky
*/

function parse_only($parser,$file,$current_file,$rc,$jexaml,$dir){
    global $passed_cnt,$failed_cnt;

    $path_to_test = realpath($dir .'/'.$file);
    // php -> php7.4
    exec('php7.4 '.$parser.' < \''.$dir . '/' . $file . '\' > mytemp_file_jexam.xml',$parse_out,$parse_retval);

    if($rc == $parse_retval){
        if ($rc == 0){
            // java compare
            $temp = "mytemp_file_jexam.xml";
            // /pub/courses/ipp/jexamxml/options
            exec('java -jar '.$jexaml.' '.$temp.' \''.$current_file . ".out' /dev/null /pub/courses/ipp/jexamxml/options",$java_out,$java_retval);
            unlink($temp);
            if($java_retval){
                $failed_cnt++;
                // throw error
                $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$parse_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
                fwrite(STDOUT,$fail."\n");
            }else{
                $passed_cnt++;
                // javacompare ok
                $pass = '<tr> <td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$parse_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
                fwrite(STDOUT,$pass."\n");
            }
        }else{
            // no javacompare but ok
            $passed_cnt++;
            $pass = '<tr><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$parse_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
            fwrite(STDOUT,$pass."\n");
        }
    } else{
        // rc codes doesnt match, throw error.
        $failed_cnt++;
        $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$parse_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
        fwrite(STDOUT,$fail."\n");
    }
}

/* Kontrola a prípadné vytvorenie nových súborov testov */

function touch_files($current_file){
    if (!file_exists($current_file . ".in")){
        touch($current_file . ".in");
    }
    if (!file_exists($current_file . ".out")){
        touch($current_file . ".out");
    }
    if (!file_exists($current_file . ".rc")){
        file_put_contents($current_file . ".rc", '0');
        return 0;
    } else{
        return file_get_contents($current_file . ".rc");
    }
}


/* Funkcia použitá v prípade parse-only parametru
* $interpreter - názov alebo cesta k súboru interpret.py
* $file - názov a cesta aktuálneho testu
* $current_file - názov aktuálneho testu bez prípony
* $rc - očakávaný návratový kód 
* $dir - názov aktuálnej zložky
*/


function int_only($interpreter,$file,$current_file,$rc,$dir){
    global $passed_cnt,$failed_cnt;
    $path_to_test = realpath($dir .'/'.$file);
    // python -> python3.8
    exec('python3.8 '.$interpreter.' --source=\''.$current_file.'.src'.'\' --input=\''.$current_file.'.in'.'\' > mytemp_file.out',$int_out,$int_retval);
    if ($rc == $int_retval){
        if ($rc == 0){
            $temp = "mytemp_file.out";
            exec('diff '.$temp.' \''.$current_file . ".out'",$diff_out,$diff_retval);
            unlink("mytemp_file.out");
            if($diff_retval){
                $failed_cnt++;
                // throw error
                $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
                fwrite(STDOUT,$fail."\n");
            }else{
                $passed_cnt++;
                // diff ok
                $pass = '<tr> <td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
                fwrite(STDOUT,$pass."\n");
            }
        }else{
            // no diff but ok
            $passed_cnt++;
            $pass = '<tr><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
            fwrite(STDOUT,$pass."\n");
        }
    } else{
        $failed_cnt++;
        $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
        fwrite(STDOUT,$fail."\n");
    }
}

/* Funkcia použitá v prípade parse-only parametru
* $parser - názov alebo cesta k súboru parse.php
* $interpreter - názov alebo cesta k súboru interpret.py
* $file - názov a cesta aktuálneho testu
* $current_file - názov aktuálneho testu bez prípony
* $rc - očakávaný návratový kód 
* $jexaml - názov alebo cesta k súboru jexaml.jar 
* $dir - názov aktuálnej zložky
*/


function both($parser,$interpreter,$file,$current_file,$rc,$jexaml,$dir){
    $path_to_test = realpath($dir .'/'.$file);

    global $passed_cnt,$failed_cnt;
    $parser_out_file = "mytemp_file_parser.xml";
    // php > php7.4
    exec('php7.4 '.$parser.' < \''.$dir . '/' . $file . '\' > mytemp_file_parser.xml',$parse_out,$parse_retval);
    if($rc == 21 || $rc  == 22 || $rc == 23 || $rc == 10){
        if($rc == $parse_retval){
            if ($rc != 0){
                // no javacompare but ok
                $passed_cnt++;
                $pass = '<tr><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$parse_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
                fwrite(STDOUT,$pass."\n");
                return;
            }
        } else{
            // rc codes doesnt match, throw error.
            $failed_cnt++;
            $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$parse_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
            fwrite(STDOUT,$fail."\n");
            return;
        }
    }

    // python > python3.8
    exec('python3.8 '.$interpreter.' --source=\''.$parser_out_file.'\' --input=\''.$current_file.'.in'.'\' > mytemp_file.out',$int_out,$int_retval);
    
    

    if ($rc == $int_retval){
        if ($rc == 0){
            $temp = "mytemp_file.out";
            exec('diff '.$temp.' \''.$current_file . ".out'",$diff_out,$diff_retval);
            unlink("mytemp_file.out");
            if($diff_retval){
                $failed_cnt++;
                // throw error
                $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
                fwrite(STDOUT,$fail."\n");
            }else{
                $passed_cnt++;
                // diff ok
                $pass = '<tr> <td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
                fwrite(STDOUT,$pass."\n");
            }
        }else{
            // no diff but ok
            $passed_cnt++;
            $pass = '<tr><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="passed">Prešiel</td></tr>';
            fwrite(STDOUT,$pass."\n");
        }
    } else{
        $failed_cnt++;
        $fail = '<tr id="fails"><td>'.intval($failed_cnt+$passed_cnt).'</td><td>'.$path_to_test.'</td><td>'.$int_retval.'</td><td>'.$rc.'</td><td class="failed">Neprešiel</td></tr>';
        fwrite(STDOUT,$fail."\n");
    }
    unlink($parser_out_file);
    
}

/* Kontrola testovych súborov a prípadné vytvorenie nových */

function check_files($dir,$file,$filename,$parser,$interpreter,$jexaml){
    global $passed_cnt,$failed_cnt,$parse_only,$int_only;
    $current_file = $dir . '/' . $filename[0];
    // check files and create if non existent
    $rc = touch_files($current_file);
    
    // execute test
    if ($parse_only){
        parse_only($parser,$file,$current_file,$rc,$jexaml,$dir);
    } elseif($int_only){
        int_only($interpreter,$file,$current_file,$rc,$dir);
    } else{
        both($parser,$interpreter,$file,$current_file,$rc,$jexaml,$dir);
    }

}

/* Kontrola zadanej zložky a inicializácia testovania */

function check_dir($dir,$recursive,$parser,$interpreter,$jexaml){
    $dir_files = scandir($dir);
    foreach($dir_files as $file){
        if($file != "." && $file != ".."){
            if (is_dir($dir . '/' . $file) && $recursive) {
                check_dir($dir . '/' . $file,$recursive,$parser,$interpreter,$jexaml);
            } elseif(!is_dir($dir . '/' . $file)){
                $filename = explode(".",$file);
                if (count($filename) != 2){
                    continue;
                }
                if ($filename[1] === "src"){
                    check_files($dir,$file,$filename,$parser,$interpreter,$jexaml);
                }
            }
        } 
    }
}

/* Inicializácia html výsledku */

function html_init(){
    $html_header = '<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>IPP Testovací skript</title>
        <style>
            body{
            margin: 0 auto;
            font-family: Arial,helvetica,sans-serif;
            }
            .header{
            text-align: center;
            background-color: dodgerblue;
            padding: 20px;
            }
            .header h1{
            color: white;
            }
            .cols{
            width: 100%;
            }
            .left{
            float: left;
            width: 50%;
            padding: 50px;
            }
            .subleft{
            float: left;
            width: 50%;
            padding: 10px;
            }
            .right{
                position: fixed;
                width: 30%;
                right: 50px;
                padding: 50px;
            }
            .subright{
            float: left;
            width: 40%;
            padding: 10px;
            }
            .clearfix::after{
            content: "";
            clear: both;
            display: table;
            }
            .subcol{
                width: 100%;
            }
    
            table {
            border-collapse: collapse;
            width: 100%;
            }
            th{
            background-color: DodgerBlue;
            color: white;
            border: 1px solid white;
            }
            th, td {
            text-align: center;
            padding: 8px;
            }
            .passed{
                background-color: #19e680;
                color:white;
                font-weight:bold;
            }
            .failed{
                background-color: #ec1313;
                color:white;
                font-weight:bold;
            }
            .jump{
                background-color: white;
                border: 2px solid dodgerblue;
                color: black;
                padding: 16px 32px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 14px 14px;
                transition-duration: 0.4s;
                cursor: pointer;
            }
            .jump:hover{
                background-color: dodgerblue;
                color:white;
            }
    
            tr:nth-child(even) {background-color: #f2f2f2;}
    
        </style>
    </head>

    
    <body>
        <div class="header">
        <h1>Výsledky testovania IPP</h1>
        </div>

        <div class="cols clearfix">
        <div class="left">
        <h3>Výsledková tabulka</h3>
        <table>
        <tr>
        <th>#</th>
        <th>Názov testu</th>
        <th>Návratový kód</th>
        <th>Očakávaný kód</th>
        <th>Status</th>
        </tr>';

    fwrite(STDOUT,$html_header);
}


/* Zakončenie html výsledku kodu */

function html_close(){
    $html_footer = '
            </div>
        </div>
    </div>
    </div>
    </body>
    </html>';
    fwrite(STDOUT,$html_footer);
}



// Nastavenie názvu skriptov a zložiek
if(!isset($dir)){
    $dir = getcwd();    
}
if(isset($parser)){
    if(!is_file($parser)){
        exit(11);
    }
} else{
    $parser = "parse.php";
    if(!is_file($parser)){
        exit(11);
    }
}
if(isset($interpreter)){
    if(!is_file($interpreter)){
        exit(11);
    }
} else{
    $interpreter = "interpret.py";
    if(!is_file($interpreter)){
        exit(11);
    }
}
if(isset($jexaml)){
    if(!is_file($jexaml)){
        exit(11);
    }    
} else{
    $jexaml = "/pub/courses/ipp/jexamxml/jexamxml.jar";
}


/* Výsledky testovania a ich zápis do html */
function stats($argv,$dir,$parser,$interpreter,$jexaml){
    global $passed_cnt,$failed_cnt;

    $args_str = "";
    foreach($argv as $arg){
        if($arg == "--help"){
            $args_str = $args_str . '<li>--help</li>';
        }
        if(preg_match('/^--directory=(\.){0,2}(\/*[a-zA-Z]*\d*\S*)*$/',$arg)){
            $args_str = $args_str . '<li>--directory='.$dir.'</li>';
        }
        if($arg == "--recursive"){
            $args_str = $args_str . '<li>--recursive</li>';
        }
        if(preg_match('/^--parse-script=(\.){0,2}(\/*[a-zA-Z]*\d*\.*)*$/',$arg)){
            $args_str = $args_str . '<li>--parse-script='.$parser.'</li>';
        }
        if(preg_match('/^--int-script=(\.){0,2}(\/*[a-zA-Z]*\d*\.*)*$/',$arg)){
            $args_str = $args_str . '<li>--int-script='.$interpreter.'</li>';
        }
        if($arg == "--parse-only"){
            $args_str = $args_str . '<li>--parse-only</li>';
        }
        if($arg == "--int-only"){
            $args_str = $args_str . '<li>--int-only</li>';
        }
        if(preg_match('/^--jexamxml=(\.){0,2}(\/*[a-zA-Z]*\d*\.*)*$/',$arg)){
            $args_str = $args_str . '<li>--jexamxml='.$jexaml.'</li>';
        }
        
    }
    if(intval($failed_cnt+$passed_cnt) == 0){
        exit (99);
    }

    if($failed_cnt != 0){
        $button = '<button class="jump" onclick="window.location.href=\'#fails\'" >Prejsť na prvý zlyhaný test</button>';
    } else{
        $button = '<p> Všetky testy prešli v poriadku!</p>';
    }
    $str = '
    </table>
    </div>
    <div class="right">
        <h3>Štatistika</h3>
        <div class="subcol clearfix">
            <div class="subleft">
                <h4>Zoznam zadaných parametrov</h4>
                <ul>' . $args_str .
                '
                </ul>  
            </div>
            <div class="subright">
            <h4>Úspešnosť testovania</h4>
            <table>
            <tr>
            <th>Testov spolu</th>
            <td>'.intval($failed_cnt+$passed_cnt).'</td>
            </tr>
            <tr>
            <th>Prešlo</th>
            <td>'.$passed_cnt.'</td>
            </tr>
            <tr>
            <th>Neprešlo</th>
            <td>'.$failed_cnt.'</td>
            </tr>
            <tr>
            <th>Úspešnosť</th>
            <td>'.round((($passed_cnt / intval($failed_cnt+$passed_cnt)) * 100),5).' %</td>
            </tr>
        </table>' . $button;

    fwrite(STDOUT,$str);
}

// inicializuj html
html_init();

// skontroluj zložku a zavolaj testovanie
check_dir($dir,$recursive,$parser,$interpreter,$jexaml);

// vykreslenie sumarizácie výsledkovej tabulky
stats($argv,$dir,$parser,$interpreter,$jexaml);

//zatvorenie html a prípadne vymazanie dočasných súborov
html_close();
if(is_file("mytemp_file.out")){
    unlink("mytemp_file.out");
}
if(is_file("mytemp_file_parser.xml")){
    unlink("mytemp_file_parser.xml");
}
if(is_file("mytemp_file_jexam.xml")){
    unlink("mytemp_file_jexam.xml");
}
?>