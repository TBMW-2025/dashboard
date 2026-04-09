
const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL      = 'https://rnuuhgiqymukzojiflry.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_b6rarUwhnIA7kwBM3ouksw_0ROLtcSa';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function checkData() {
    console.log('--- PLACEMENTS ---');
    const { data: p } = await supabase.from('placements').select('*').limit(3);
    console.log(JSON.stringify(p, null, 2));

    console.log('--- INTERNSHIPS ---');
    const { data: i } = await supabase.from('internships').select('*').limit(3);
    console.log(JSON.stringify(i, null, 2));
}

checkData();
