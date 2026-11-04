<?php
// Test helper: extract actual named functions without executing a CLI entry point.
function pctFixtureFunctions($file, array $wanted) {
    $tokens = token_get_all(file_get_contents($file));
    $result = '';
    for ($i = 0; $i < count($tokens); $i++) {
        if (!is_array($tokens[$i]) || $tokens[$i][0] !== T_FUNCTION) continue;
        $nameIndex = $i + 1;
        while (is_array($tokens[$nameIndex]) && $tokens[$nameIndex][0] === T_WHITESPACE) $nameIndex++;
        if (!is_array($tokens[$nameIndex]) || $tokens[$nameIndex][0] !== T_STRING) continue;
        $name = $tokens[$nameIndex][1];
        if (!in_array($name, $wanted, true)) continue;
        $text = ''; $depth = 0; $body = false;
        do {
            $token = $tokens[$i++];
            $text .= is_array($token) ? $token[1] : $token;
            if ($token === '{') { $body = true; $depth++; }
            if ($token === '}') $depth--;
        } while (!$body || $depth > 0);
        $i--;
        $result .= $text . "\n";
    }
    return $result;
}
