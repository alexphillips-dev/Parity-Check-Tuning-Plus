<?php
// Tokenize owned runtime code without executing host entry points.
$files = array_merge(glob($argv[1].'/*.php'), glob($argv[1].'/*.page'));
$inventory = []; $definitions = [];
foreach ($files as $file) {
    $tokens = array_values(array_filter(token_get_all(file_get_contents($file)), static function ($token) {
        return !is_array($token) || !in_array($token[0], [T_WHITESPACE,T_COMMENT,T_DOC_COMMENT], true);
    }));
    $spans = [];
    foreach ($tokens as $index => $token) {
        if (!is_array($token) || $token[0] !== T_FUNCTION || !is_array($tokens[$index+1] ?? null)
            || $tokens[$index+1][0] !== T_STRING) continue;
        $name = $tokens[$index+1][1]; $open = $index+2;
        while (isset($tokens[$open]) && $tokens[$open] !== '{') $open++;
        $depth = 0; $end = $open;
        do {
            $part = $tokens[$end];
            if ($part === '{' || (is_array($part) && in_array($part[0], [T_CURLY_OPEN,T_DOLLAR_OPEN_CURLY_BRACES], true))) $depth++;
            if ($part === '}') $depth--;
            $end++;
        } while ($depth > 0 && isset($tokens[$end]));
        $id = basename($file).'::'.strtolower($name);
        $spans[] = ['start'=>$index,'end'=>$end-1,'id'=>$id];
        $definitions[$id] = ['name'=>$name,'file'=>basename($file),'line'=>$token[2]];
    }
    $inventory[] = ['file'=>$file,'tokens'=>$tokens,'spans'=>$spans];
}
$edges = []; $roots = [];
foreach ($inventory as $item) {
    $root = basename($item['file']).'::<entry>'; $roots[] = $root; $edges[$root] = [];
    foreach ($item['tokens'] as $index => $token) {
        if (!is_array($token)) continue;
        $caller = $root;
        foreach ($item['spans'] as $span) if ($index >= $span['start'] && $index <= $span['end']) $caller = $span['id'];
        $name = null;
        if (in_array($token[0], [T_STRING,T_NAME_QUALIFIED,T_NAME_FULLY_QUALIFIED], true)
            && ($item['tokens'][$index+1] ?? null) === '(') {
            $previous = $item['tokens'][$index-1] ?? null;
            if (is_array($previous) && in_array($previous[0], [T_FUNCTION,T_OBJECT_OPERATOR,T_DOUBLE_COLON], true)) continue;
            $name = ltrim($token[1], '\\');
        } elseif ($token[0] === T_CONSTANT_ENCAPSED_STRING) {
            // Literal function names can be callbacks; existence checks do not invoke them.
            $before = $item['tokens'][$index-2] ?? null;
            if (is_array($before) && strtolower($before[1]) === 'function_exists') continue;
            $name = substr($token[1], 1, -1);
        }
        if ($name === null) continue;
        foreach ($definitions as $id => $definition) {
            if (strcasecmp($name, $definition['name']) === 0) $edges[$caller][] = $id;
        }
    }
}
echo json_encode(['definitions'=>$definitions,'edges'=>$edges,'roots'=>$roots]);
