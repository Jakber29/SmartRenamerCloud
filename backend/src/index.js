// Smart Renamer Cloud API - Cloudflare Worker
// This replaces the Flask backend with a serverless API

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    };

    // Handle CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // API Routes
      if (path.startsWith('/api/')) {
        return await handleApiRequest(request, env, path, method, corsHeaders);
      }

      // Serve static files (for development)
      if (path === '/' || path === '/index.html') {
        return new Response('Smart Renamer Cloud - API Server', {
          headers: { ...corsHeaders, 'Content-Type': 'text/plain' }
        });
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};

async function handleApiRequest(request, env, path, method, corsHeaders) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  // Parse JSON body for POST/PUT requests
  let body = null;
  if (method === 'POST' || method === 'PUT') {
    try {
      body = await request.json();
    } catch (e) {
      // Handle non-JSON requests (like file uploads)
      body = {};
    }
  }

  // Route handlers
  switch (path) {
    case '/api/test':
      return new Response(JSON.stringify({ success: true, message: 'API is working!' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });

    case '/api/vendors':
      return await handleVendors(request, env, method, body, searchParams, corsHeaders);

    case '/api/projects':
      return await handleProjects(request, env, method, body, searchParams, corsHeaders);

    case '/api/team-members':
      return await handleTeamMembers(request, env, method, body, searchParams, corsHeaders);

    case '/api/transactions':
      return await handleTransactions(request, env, method, body, searchParams, corsHeaders);

    case '/api/csv-transactions':
      return await handleCsvTransactions(request, env, method, body, searchParams, corsHeaders);

    case '/api/manual-matches':
      return await handleManualMatches(request, env, method, body, searchParams, corsHeaders);

    case '/api/manual-match':
      return await handleManualMatch(request, env, method, body, searchParams, corsHeaders);

    case '/api/upload-csv':
      return await handleUploadCsv(request, env, method, body, searchParams, corsHeaders);

    case '/api/reimbursements':
      return await handleReimbursements(request, env, method, body, searchParams, corsHeaders);

    case '/api/transaction-tags':
      return await handleTransactionTags(request, env, method, body, searchParams, corsHeaders);

    case '/api/files':
      return await handleFiles(request, env, method, body, searchParams, corsHeaders);

    case '/api/rename':
      return await handleRename(request, env, method, body, searchParams, corsHeaders);

    case '/api/upload':
      return await handleFileUpload(request, env, method, body, searchParams, corsHeaders);

    default:
      return new Response(JSON.stringify({ error: 'Endpoint not found' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
  }
}

// Database helper functions
async function getDb(env) {
  return env.DB;
}

// Vendor management
async function handleVendors(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const query = searchParams.get('q') || '';
    const limit = parseInt(searchParams.get('limit') || '10000');
    
    let vendors = await getAllVendors(db);
    
    if (query) {
      vendors = vendors.filter(vendor => 
        vendor.name.toLowerCase().includes(query.toLowerCase())
      );
    }
    
    vendors = vendors.slice(0, limit);
    
    return new Response(JSON.stringify({
      success: true,
      vendors,
      total: vendors.length,
      query
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  if (method === 'POST') {
    if (!body || !body.name) {
      return new Response(JSON.stringify({ error: 'Vendor name is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const vendorName = body.name.trim();
    if (!vendorName) {
      return new Response(JSON.stringify({ error: 'Vendor name cannot be empty' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const vendors = await getAllVendors(db);
    
    // Check for duplicates
    const existingVendor = vendors.find(v => v.name.toLowerCase() === vendorName.toLowerCase());
    if (existingVendor) {
      return new Response(JSON.stringify({ error: 'Vendor already exists' }), {
        status: 409,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const newVendor = {
      id: String(vendors.length + 1),
      name: vendorName,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    if (body.description) newVendor.description = body.description.trim();
    if (body.contact) newVendor.contact = body.contact.trim();
    if (body.phone) newVendor.phone = body.phone.trim();
    if (body.email) newVendor.email = body.email.trim();
    if (body.address) newVendor.address = body.address.trim();
    
    vendors.push(newVendor);
    await saveVendors(db, vendors);
    
    return new Response(JSON.stringify({
      success: true,
      vendor: newVendor,
      message: 'Vendor created successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Project management
async function handleProjects(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const query = searchParams.get('q') || '';
    const limit = parseInt(searchParams.get('limit') || '10000');
    
    let projects = await getAllProjects(db);
    
    if (query) {
      projects = projects.filter(project => 
        project.name.toLowerCase().includes(query.toLowerCase())
      );
    }
    
    projects = projects.slice(0, limit);
    
    return new Response(JSON.stringify({
      success: true,
      projects,
      total: projects.length,
      query
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  if (method === 'POST') {
    if (!body || !body.name) {
      return new Response(JSON.stringify({ error: 'Project name is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const projectName = body.name.trim();
    if (!projectName) {
      return new Response(JSON.stringify({ error: 'Project name cannot be empty' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const projects = await getAllProjects(db);
    
    // Check for duplicates
    const existingProject = projects.find(p => p.name.toLowerCase() === projectName.toLowerCase());
    if (existingProject) {
      return new Response(JSON.stringify({ error: 'Project already exists' }), {
        status: 409,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const newProject = {
      id: String(projects.length + 1),
      name: projectName,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    if (body.description) newProject.description = body.description.trim();
    if (body.client) newProject.client = body.client.trim();
    if (body.status) newProject.status = body.status.trim();
    if (body.start_date) newProject.start_date = body.start_date.trim();
    if (body.end_date) newProject.end_date = body.end_date.trim();
    if (body.builders_fee !== undefined) {
      const buildersFee = parseFloat(body.builders_fee);
      if (isNaN(buildersFee) || buildersFee < 0 || buildersFee > 100) {
        return new Response(JSON.stringify({ error: 'Builders fee must be between 0 and 100' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      newProject.builders_fee = buildersFee;
    }
    
    projects.push(newProject);
    await saveProjects(db, projects);
    
    return new Response(JSON.stringify({
      success: true,
      project: newProject,
      message: 'Project created successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Team member management
async function handleTeamMembers(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const query = searchParams.get('q') || '';
    const limit = parseInt(searchParams.get('limit') || '10000');
    
    let teamMembers = await getAllTeamMembers(db);
    
    if (query) {
      teamMembers = teamMembers.filter(member => 
        member.name.toLowerCase().includes(query.toLowerCase())
      );
    }
    
    teamMembers = teamMembers.slice(0, limit);
    
    return new Response(JSON.stringify({
      success: true,
      team_members: teamMembers,
      total: teamMembers.length,
      query
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  if (method === 'POST') {
    if (!body || !body.name) {
      return new Response(JSON.stringify({ error: 'Team member name is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const name = body.name.trim();
    if (!name) {
      return new Response(JSON.stringify({ error: 'Team member name cannot be empty' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const teamMembers = await getAllTeamMembers(db);
    
    // Check for duplicates
    const existingMember = teamMembers.find(m => m.name.toLowerCase() === name.toLowerCase());
    if (existingMember) {
      return new Response(JSON.stringify({ error: 'Team member already exists' }), {
        status: 409,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // Validate card last four if provided
    const cardLastFour = body.card_last_four?.trim();
    if (cardLastFour) {
      if (!cardLastFour.match(/^\d{4}$/)) {
        return new Response(JSON.stringify({ error: 'Card last four must be exactly 4 digits' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      // Check if card number is already used
      const existingCard = teamMembers.find(m => m.card_last_four === cardLastFour);
      if (existingCard) {
        return new Response(JSON.stringify({ 
          error: `Card number ${cardLastFour} is already assigned to ${existingCard.name}` 
        }), {
          status: 409,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }
    
    const newMember = {
      id: String(teamMembers.length + 1),
      name,
      card_last_four: cardLastFour || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    if (body.title) newMember.title = body.title.trim();
    if (body.department) newMember.department = body.department.trim();
    if (body.email) newMember.email = body.email.trim();
    
    teamMembers.push(newMember);
    await saveTeamMembers(db, teamMembers);
    
    return new Response(JSON.stringify({
      success: true,
      team_member: newMember,
      message: 'Team member created successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Transaction management
async function handleTransactions(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const transactions = await getAllTransactions(db);
    
    // Add cardholder mapping
    const cardHolders = {
      '2321': 'David Berman',
      '2734': 'Sharon Joch',
      '4295': 'Genaliah Bloch',
      '0684': 'Alexis Linares',
      '7567': 'Jaqueline Padgett',
      '9203': 'Juan Vargas',
      '0205': 'Jhonatan Salazar',
      '2982': 'Luis Leon',
      '9780': 'Sergio Blanco',
      '7471': 'Yas Shahrestani',
      '5682': 'Edy Moncada',
      '1347': 'Sharon Joch (NEW)'
    };
    
    const processedTransactions = transactions.map(transaction => {
      const processedTransaction = { ...transaction };
      const description = transaction.description || '';
      const last4 = description.slice(-4).padStart(4, '0');
      processedTransaction.cardholder = cardHolders[last4] || 'Unknown';
      return processedTransaction;
    });
    
    return new Response(JSON.stringify({
      success: true,
      transactions: processedTransactions,
      count: processedTransactions.length
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// CSV Transactions (alias for transactions)
async function handleCsvTransactions(request, env, method, body, searchParams, corsHeaders) {
  return await handleTransactions(request, env, method, body, searchParams, corsHeaders);
}

// Manual matches
async function handleManualMatches(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const matches = await getAllManualMatches(db);
    
    return new Response(JSON.stringify({
      success: true,
      matches
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Manual match creation
async function handleManualMatch(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'POST') {
    if (!body || !body.filename) {
      return new Response(JSON.stringify({ error: 'Filename is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const { filename, transaction_index, force = false } = body;
    
    if (transaction_index === undefined) {
      return new Response(JSON.stringify({ error: 'Transaction index is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const matches = await getAllManualMatches(db);
    const transactions = await getAllTransactions(db);
    
    if (transaction_index === -1) {
      // Clear the match
      delete matches[filename];
      await saveManualMatches(db, matches);
      
      return new Response(JSON.stringify({
        success: true,
        message: 'Match cleared successfully'
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // Validate transaction index
    if (transaction_index < 0 || transaction_index >= transactions.length) {
      return new Response(JSON.stringify({
        error: `Invalid transaction index: ${transaction_index}. Must be between 0 and ${transactions.length - 1}`
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // Check for conflicts unless forcing
    if (!force) {
      const conflicts = checkDuplicateAssignments(matches, filename, transaction_index);
      
      if (conflicts.transaction_conflict) {
        const transaction = transactions[transaction_index];
        return new Response(JSON.stringify({
          error: 'duplicate_transaction',
          message: `Transaction "${transaction.vendor || 'Unknown'} - $${transaction.amount || '0'}" is already assigned to file "${conflicts.transaction_conflict}"`,
          conflict_file: conflicts.transaction_conflict,
          transaction,
          transaction_index
        }), {
          status: 409,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      if (conflicts.file_conflict !== undefined) {
        const existingTransaction = transactions[conflicts.file_conflict];
        return new Response(JSON.stringify({
          error: 'duplicate_file',
          message: `File "${filename}" is already assigned to transaction "${existingTransaction.vendor || 'Unknown'} - $${existingTransaction.amount || '0'}"`,
          conflict_transaction: existingTransaction,
          conflict_transaction_index: conflicts.file_conflict
        }), {
          status: 409,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // Create the match
    matches[filename] = transaction_index;
    await saveManualMatches(db, matches);
    
    return new Response(JSON.stringify({
      success: true,
      message: 'Match created successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// CSV Upload
async function handleUploadCsv(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'POST') {
    // This is a simplified version - in a real implementation,
    // you'd need to handle multipart form data for file uploads
    // For now, we'll assume the CSV data is sent as JSON
    
    if (!body || !body.csv_data) {
      return new Response(JSON.stringify({ error: 'CSV data is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    try {
      const transactions = parseCsvData(body.csv_data);
      await saveTransactions(db, transactions);
      
      return new Response(JSON.stringify({
        success: true,
        message: `Successfully loaded ${transactions.length} transactions`,
        transactions_count: transactions.length
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Reimbursements
async function handleReimbursements(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const reimbursements = await getAllReimbursements(db);
    
    return new Response(JSON.stringify({
      success: true,
      reimbursements
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  if (method === 'POST') {
    if (!body || !body.vendor || !body.amount || !body.date) {
      return new Response(JSON.stringify({ error: 'Vendor, amount, and date are required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const reimbursements = await getAllReimbursements(db);
    
    const newReimbursement = {
      id: reimbursements.length + 1,
      vendor: body.vendor.trim(),
      amount: parseFloat(body.amount),
      date: body.date.trim(),
      description: body.description?.trim() || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    reimbursements.push(newReimbursement);
    await saveReimbursements(db, reimbursements);
    
    return new Response(JSON.stringify({
      success: true,
      reimbursement: newReimbursement,
      message: 'Reimbursement created successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Transaction tags
async function handleTransactionTags(request, env, method, body, searchParams, corsHeaders) {
  const db = await getDb(env);
  
  if (method === 'GET') {
    const tags = await getAllTransactionTags(db);
    
    return new Response(JSON.stringify({
      success: true,
      tags
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  if (method === 'POST') {
    if (!body || !body.tags) {
      return new Response(JSON.stringify({ error: 'Tags data is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    const tags = body.tags;
    await saveTransactionTags(db, tags);
    
    return new Response(JSON.stringify({
      success: true,
      message: 'Tags saved successfully'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// File management (simplified for cloud version)
async function handleFiles(request, env, method, body, searchParams, corsHeaders) {
  if (method === 'GET') {
    // In the cloud version, files are stored in R2
    // This is a simplified implementation
    return new Response(JSON.stringify({
      files: [],
      folder: null,
      csv_loaded: false,
      transactions_count: 0,
      no_folder_selected: true
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// File rename (simplified for cloud version)
async function handleRename(request, env, method, body, searchParams, corsHeaders) {
  if (method === 'POST') {
    // In the cloud version, file operations would be handled through R2
    // This is a simplified implementation
    return new Response(JSON.stringify({
      success: true,
      message: 'File rename operation would be implemented with R2 storage'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// File upload (simplified for cloud version)
async function handleFileUpload(request, env, method, body, searchParams, corsHeaders) {
  if (method === 'POST') {
    // In the cloud version, file uploads would be handled through R2
    // This is a simplified implementation
    return new Response(JSON.stringify({
      success: true,
      message: 'File upload would be implemented with R2 storage'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Helper functions for database operations
async function getAllVendors(db) {
  try {
    const result = await db.prepare('SELECT * FROM vendors ORDER BY name').all();
    return result.results || [];
  } catch (error) {
    console.error('Error getting vendors:', error);
    return [];
  }
}

async function saveVendors(db, vendors) {
  try {
    // Clear existing vendors
    await db.prepare('DELETE FROM vendors').run();
    
    // Insert new vendors
    for (const vendor of vendors) {
      await db.prepare(`
        INSERT INTO vendors (id, name, description, contact, phone, email, address, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        vendor.id,
        vendor.name,
        vendor.description || '',
        vendor.contact || '',
        vendor.phone || '',
        vendor.email || '',
        vendor.address || '',
        vendor.created_at,
        vendor.updated_at
      ).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving vendors:', error);
    return false;
  }
}

async function getAllProjects(db) {
  try {
    const result = await db.prepare('SELECT * FROM projects ORDER BY name').all();
    return result.results || [];
  } catch (error) {
    console.error('Error getting projects:', error);
    return [];
  }
}

async function saveProjects(db, projects) {
  try {
    // Clear existing projects
    await db.prepare('DELETE FROM projects').run();
    
    // Insert new projects
    for (const project of projects) {
      await db.prepare(`
        INSERT INTO projects (id, name, description, client, status, start_date, end_date, builders_fee, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        project.id,
        project.name,
        project.description || '',
        project.client || '',
        project.status || '',
        project.start_date || '',
        project.end_date || '',
        project.builders_fee || 0,
        project.created_at,
        project.updated_at
      ).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving projects:', error);
    return false;
  }
}

async function getAllTeamMembers(db) {
  try {
    const result = await db.prepare('SELECT * FROM team_members ORDER BY name').all();
    return result.results || [];
  } catch (error) {
    console.error('Error getting team members:', error);
    return [];
  }
}

async function saveTeamMembers(db, teamMembers) {
  try {
    // Clear existing team members
    await db.prepare('DELETE FROM team_members').run();
    
    // Insert new team members
    for (const member of teamMembers) {
      await db.prepare(`
        INSERT INTO team_members (id, name, card_last_four, title, department, email, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        member.id,
        member.name,
        member.card_last_four || '',
        member.title || '',
        member.department || '',
        member.email || '',
        member.created_at,
        member.updated_at
      ).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving team members:', error);
    return false;
  }
}

async function getAllTransactions(db) {
  try {
    const result = await db.prepare('SELECT * FROM transactions ORDER BY date DESC').all();
    return result.results || [];
  } catch (error) {
    console.error('Error getting transactions:', error);
    return [];
  }
}

async function saveTransactions(db, transactions) {
  try {
    // Clear existing transactions
    await db.prepare('DELETE FROM transactions').run();
    
    // Insert new transactions
    for (const transaction of transactions) {
      await db.prepare(`
        INSERT INTO transactions (date, vendor, amount, description, transaction_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
      `).bind(
        transaction.date || '',
        transaction.vendor || '',
        transaction.amount || '',
        transaction.description || '',
        transaction.transaction_type || 'charge',
        new Date().toISOString()
      ).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving transactions:', error);
    return false;
  }
}

async function getAllManualMatches(db) {
  try {
    const result = await db.prepare('SELECT * FROM manual_matches').all();
    const matches = {};
    for (const row of result.results || []) {
      matches[row.filename] = row.transaction_index;
    }
    return matches;
  } catch (error) {
    console.error('Error getting manual matches:', error);
    return {};
  }
}

async function saveManualMatches(db, matches) {
  try {
    // Clear existing matches
    await db.prepare('DELETE FROM manual_matches').run();
    
    // Insert new matches
    for (const [filename, transactionIndex] of Object.entries(matches)) {
      await db.prepare(`
        INSERT INTO manual_matches (filename, transaction_index, created_at)
        VALUES (?, ?, ?)
      `).bind(filename, transactionIndex, new Date().toISOString()).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving manual matches:', error);
    return false;
  }
}

async function getAllReimbursements(db) {
  try {
    const result = await db.prepare('SELECT * FROM reimbursements ORDER BY date DESC').all();
    return result.results || [];
  } catch (error) {
    console.error('Error getting reimbursements:', error);
    return [];
  }
}

async function saveReimbursements(db, reimbursements) {
  try {
    // Clear existing reimbursements
    await db.prepare('DELETE FROM reimbursements').run();
    
    // Insert new reimbursements
    for (const reimbursement of reimbursements) {
      await db.prepare(`
        INSERT INTO reimbursements (id, vendor, amount, date, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `).bind(
        reimbursement.id,
        reimbursement.vendor,
        reimbursement.amount,
        reimbursement.date,
        reimbursement.description || '',
        reimbursement.created_at,
        reimbursement.updated_at
      ).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving reimbursements:', error);
    return false;
  }
}

async function getAllTransactionTags(db) {
  try {
    const result = await db.prepare('SELECT * FROM transaction_tags').all();
    const tags = {};
    for (const row of result.results || []) {
      tags[row.transaction_index] = JSON.parse(row.tags);
    }
    return tags;
  } catch (error) {
    console.error('Error getting transaction tags:', error);
    return {};
  }
}

async function saveTransactionTags(db, tags) {
  try {
    // Clear existing tags
    await db.prepare('DELETE FROM transaction_tags').run();
    
    // Insert new tags
    for (const [transactionIndex, tagList] of Object.entries(tags)) {
      await db.prepare(`
        INSERT INTO transaction_tags (transaction_index, tags, created_at)
        VALUES (?, ?, ?)
      `).bind(transactionIndex, JSON.stringify(tagList), new Date().toISOString()).run();
    }
    return true;
  } catch (error) {
    console.error('Error saving transaction tags:', error);
    return false;
  }
}

// Helper functions
function checkDuplicateAssignments(matches, filename, transactionIndex) {
  const conflicts = {
    transaction_conflict: null,
    file_conflict: null
  };
  
  // Check if this transaction is already assigned to another file
  for (const [existingFilename, existingIndex] of Object.entries(matches)) {
    if (existingIndex === transactionIndex && existingFilename !== filename) {
      conflicts.transaction_conflict = existingFilename;
      break;
    }
  }
  
  // Check if this file is already assigned to another transaction
  if (filename in matches && matches[filename] !== transactionIndex) {
    conflicts.file_conflict = matches[filename];
  }
  
  return conflicts;
}

function parseCsvData(csvData) {
  // Simple CSV parsing - in a real implementation, you'd use a proper CSV parser
  const lines = csvData.split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  const transactions = [];
  
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    
    const values = lines[i].split(',').map(v => v.trim());
    const transaction = {};
    
    headers.forEach((header, index) => {
      transaction[header.toLowerCase()] = values[index] || '';
    });
    
    // Normalize field names
    if (transaction.date) transaction.date = transaction.date;
    if (transaction.payee) transaction.vendor = transaction.payee;
    if (transaction.vendor) transaction.vendor = transaction.vendor;
    if (transaction.spent) {
      transaction.amount = transaction.spent.replace('$', '').replace(',', '');
      transaction.transaction_type = 'charge';
    } else if (transaction.received) {
      const amount = parseFloat(transaction.received.replace('$', '').replace(',', ''));
      transaction.amount = String(-amount);
      transaction.transaction_type = 'credit';
    } else if (transaction.amount) {
      transaction.amount = transaction.amount.replace('$', '').replace(',', '');
      transaction.transaction_type = 'charge';
    }
    if (transaction.description) transaction.description = transaction.description;
    
    transactions.push(transaction);
  }
  
  return transactions;
} 